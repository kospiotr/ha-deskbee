# Architecture & Technical Documentation

## Overview

`ha-deskbee` is a custom [Home Assistant](https://www.home-assistant.io/) integration that connects to the [Deskbee](https://deskbee.com/) desk/parking booking SaaS. It exposes reservation state as HA sensors and lets users create bookings via HA actions (services), enabling automation of workplace reservations.

---

## Repository Layout

```
custom_components/deskbee/
├── __init__.py          # Integration entry point, service registration
├── config_flow.py       # UI setup wizard and options flow
├── coordinator.py       # Deskbee API client + polling coordinator
├── sensor.py            # All sensor entity classes
├── const.py             # Shared constants
├── services.yaml        # Service UI schema (Developer Tools)
├── strings.json         # UI label source
└── translations/
    └── en.json          # English UI labels
```

---

## Data Flow

```
Home Assistant startup
        │
        ▼
 async_setup_entry()          ← __init__.py
        │
        ├─ creates DeskbeeCoordinator
        │         │
        │         └─ first refresh → GET /api/bookings/me  ← Deskbee Cloud API
        │
        ├─ stores coordinator in hass.data[DOMAIN][entry_id]
        │
        ├─ forwards to sensor platform → async_setup_entry()  ← sensor.py
        │         │
        │         └─ creates sensor entities (all read from coordinator.data)
        │
        ├─ registers deskbee.create_reservation service
        │
        └─ registers per-booking-template services
                  (e.g. deskbee.office_book_today)

Every 30 minutes:
        DeskbeeCoordinator._async_update_data()
                │
                └─ GET /api/bookings/me  →  coordinator.data updated
                          │
                          └─ all CoordinatorEntity sensors notify HA of new state

User triggers a service:
        deskbee.create_reservation  (or booking template service)
                │
                └─ POST /api/bookings  (try UUIDs in order until one succeeds)
                          │
                          └─ coordinator.async_request_refresh()
                                    │
                                    └─ sensors update immediately
```

---

## Module Reference

### `const.py`

Defines the three shared string constants used across all modules:

| Constant | Value | Purpose |
|---|---|---|
| `DOMAIN` | `"deskbee"` | HA integration domain key |
| `CONF_DOMAIN` | `"domain"` | Config entry key for the Deskbee account name |
| `CONF_BOOKINGS` | `"bookings"` | Options entry key for booking templates list |

---

### `coordinator.py` — `DeskbeeCoordinator`

Extends `DataUpdateCoordinator[list[dict]]`. Holds the Deskbee account name and JWT token; owns all HTTP communication.

**Poll interval:** 30 minutes (`_UPDATE_INTERVAL`).

**`_async_update_data()`** — called automatically by HA on the poll interval:
- `GET https://api.deskbee.io/api/bookings/me`
- Query params request page 1, limit 10, with full includes (service, checkin, type, parking, etc.)
- Required headers: `Authorization: Bearer <token>`, `x-app-account: <domain>`, `x-app-version: 1.237.6060`
- Returns `response["data"]` as `list[dict]` — stored in `coordinator.data`
- Raises `UpdateFailed` on any HTTP or network error (HA marks sensors unavailable)

**`async_create_reservation()`** — called by service handlers on demand:
- `POST https://api.deskbee.io/api/bookings`
- Body: `{ uuid, start_date (DD/MM/YYYY), start_hour (HH:MM), end_date, end_hour, reason, booking_uuid_identifier: null }`
- Raises `ClientResponseError` on failure (callers catch this to try the next UUID)

Uses HA's shared `aiohttp` session (`async_get_clientsession`) — no extra dependencies.

---

### `config_flow.py`

#### `DeskbeeConfigFlow`

Initial setup wizard (appears when adding the integration from the UI).

- **Step `user`**: collects `domain` (Deskbee account name, used as `x-app-account` header) and `access_token` (JWT). No API call is made during setup — the token is validated lazily on first coordinator refresh.
- Exposes `async_get_options_flow` so HA shows a "Configure" button on the integration card.

#### `DeskbeeOptionsFlow`

Opened via Settings → Integrations → Deskbee → Configure. Manages the list of **booking templates** stored in `entry.options["bookings"]`.

**Flow steps:**

```
init (menu)
 ├─ add_booking  →  form: Name, Start Time, End Time, Place UUIDs
 │                       └─ appends to bookings list → async_create_entry
 └─ remove_booking (only shown when bookings exist)
          └─ dropdown of existing booking names → removes selected → async_create_entry
```

`async_create_entry` in an options flow saves to `entry.options` and triggers the update listener, which reloads the config entry. This causes all sensors and services derived from the booking templates to be rebuilt.

**Booking template schema** (stored in `entry.options["bookings"]`):

```python
{
    "name": str,           # display name, e.g. "Office Desk"
    "start_time": str,     # "HH:MM:SS" from TimeSelector, e.g. "08:30:00"
    "end_time": str,       # "HH:MM:SS", e.g. "17:00:00"
    "place_uuids": list[str],  # ordered list — tried in sequence on booking
}
```

---

### `__init__.py` — Integration lifecycle

#### `async_setup_entry()`

1. Instantiates `DeskbeeCoordinator` and calls `async_config_entry_first_refresh()` — if this raises, HA marks the entry as failed and shows an error in the UI.
2. Stores coordinator: `hass.data[DOMAIN][entry.entry_id] = coordinator`
3. Forwards to the `sensor` platform.
4. Registers `deskbee.create_reservation` (once across all entries — guarded by `has_service`).
5. Iterates `entry.options["bookings"]` and registers two services per template:
   - `deskbee.{slug}_book_today`
   - `deskbee.{slug}_book_tomorrow`
6. Tracks all per-booking service names: `hass.data[DOMAIN]["_booking_services"][entry_id]`
7. Attaches `_async_update_listener` — triggers `async_reload` when options change.

#### Service: `deskbee.create_reservation`

General-purpose ad-hoc booking. Parameters:

| Field | Type | Default | Notes |
|---|---|---|---|
| `place_uuids` | list[str] | required | Tried in order; first success wins |
| `date` | date | required | Target date |
| `start_time` | time | `08:30` | |
| `end_time` | time | `17:00` | |
| `reason` | str | `""` | |

**Fallback logic:** iterates `place_uuids`; on HTTP error logs a warning and tries the next. If all fail, raises `HomeAssistantError`. On success, calls `coordinator.async_request_refresh()` so sensors update immediately.

#### Per-booking services: `deskbee.{slug}_book_today` / `_book_tomorrow`

Zero-parameter services generated from each booking template. The date is computed at call time (`date.today()` ± delta). Place UUIDs and times come from the stored booking template dict. Same fallback logic as `create_reservation`.

**Cleanup in `async_unload_entry()`:**
- Removes the coordinator from `hass.data`.
- Unregisters all per-booking services for this entry.
- Unregisters `create_reservation` only when no entries remain.

---

### `sensor.py`

All sensor entities. `async_setup_entry` creates the full set from `entry.data` and `entry.options`.

#### `DeskbeeTokenExpirySensor`

- **State:** UTC datetime of JWT expiry (`device_class: TIMESTAMP`)
- **How:** Decodes the JWT payload (base64url, middle segment) with stdlib only — no signature verification. Reads the `exp` Unix timestamp.
- **Updates:** Every HA state machine poll (static, no coordinator needed)

#### `DeskbeeTokenValidSensor`

- **State:** `"valid"` or `"invalid"`
- **How:** Calls `_decode_jwt_expiry()` and compares against `datetime.now(utc)`. Returns `"invalid"` if decoding fails.

#### `DeskbeeReservationsSensor`

- **State:** Total count of upcoming reservations (integer)
- **Attributes:** `reservations` — list of summary dicts (uuid, start_date, end_date, place_type, place, area, status)
- **Updates:** Whenever `DeskbeeCoordinator` refreshes (every 30 min, or immediately after a booking action)

#### `DeskbeeBookingSensor`

One class parameterised by `when ∈ {"today", "tomorrow", "other"}`. Creates three entities per booking template.

- **State:** Count of existing reservations matching this template's place UUIDs for the given date window
- **Attributes:** `reservations` — filtered summary list
- **Filtering:**
  - Matches `r["place"]["uuid"] in booking["place_uuids"]`
  - Parses `r["start_date"]` (ISO 8601 with UTC offset) to a local `date` via `datetime.fromisoformat().date()`
  - `today`: date == today; `tomorrow`: date == today+1; `other`: date > today+1
- **Updates:** Whenever the coordinator refreshes (same data, different filter)

**Entity naming convention:**

```
sensor.{slugified_booking_name}_reservations_today
sensor.{slugified_booking_name}_reservations_tomorrow
sensor.{slugified_booking_name}_reservations_other
```

---

## State Storage: `hass.data[DOMAIN]`

```python
hass.data["deskbee"] = {
    # One entry per config entry (value is always a DeskbeeCoordinator)
    "<entry_id>": DeskbeeCoordinator,

    # Tracks which booking-template services belong to which entry
    "_booking_services": {
        "<entry_id>": ["office_book_today", "office_book_tomorrow", ...],
    },
}
```

Keys starting with `_` are internal bookkeeping; the `async_unload_entry` check for remaining entries filters them out with `not k.startswith("_")`.

---

## API Reference (Deskbee)

All requests require:
```
Authorization: Bearer <JWT>
x-app-account: <domain>        # e.g. "gft"
x-app-version: 1.237.6060
```

### `GET /api/bookings/me`

Fetches the current user's upcoming reservations.

| Param | Value |
|---|---|
| `page` | `1` |
| `limit` | `10` |
| `search` | `type:;search:;period:;filter:;uuid:` |
| `include` | `service;recurrences;meeting;calendar_integration;is_extend;resources;checkin;type;parking;tolerance;reason;parent` |

Response: `{ "data": [ <reservation>, ... ], "meta": { ... } }`

Key fields used per reservation:

| Field | Used by |
|---|---|
| `uuid` | `_reservation_summary` |
| `start_date` | date filtering in `DeskbeeBookingSensor` |
| `end_date` | `_reservation_summary` |
| `place.uuid` | booking template matching |
| `place.name_display` | `_reservation_summary` |
| `place.area_full` | `_reservation_summary` |
| `place_type` | `_reservation_summary` |
| `status.name` | `_reservation_summary` |

### `POST /api/bookings`

Creates a reservation.

```json
{
  "uuid": "<place_uuid>",
  "start_date": "20/04/2026",
  "start_hour": "08:30",
  "end_date": "20/04/2026",
  "end_hour": "17:00",
  "reason": "",
  "booking_uuid_identifier": null
}
```

Response: `{ "data": { "place_uuid", "name", "person_uuid", "booking_uuid" } }`

---

## JWT Token

The token is a standard JWT (RS256 or HS256). The integration:
1. Stores it verbatim in `entry.data["access_token"]` (HA's encrypted config entry store).
2. Sends it as `Authorization: Bearer <token>` on every request.
3. Decodes the `exp` claim client-side (base64url decode of the payload segment, no signature check) to power the expiry and validity sensors.

The token is obtained from the Deskbee web app's Local Storage under the key `desko-app-token`.

---

## Options Change Lifecycle

```
User saves options (add/remove booking template)
        │
        ▼
entry.options updated by HA
        │
        ▼
_async_update_listener() fires
        │
        ▼
hass.config_entries.async_reload(entry_id)
        │
        ├─ async_unload_entry()
        │    ├─ sensor platform unloaded (entities removed)
        │    └─ per-booking services unregistered
        │
        └─ async_setup_entry()
             ├─ coordinator recreated + refreshed
             ├─ sensor platform re-setup (new entities created)
             └─ per-booking services re-registered from updated options
```
