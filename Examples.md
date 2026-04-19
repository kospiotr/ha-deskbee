# Configuration
## Desks UUIDs 
- 48ce2c5e-ba55-428b-823d-e8ba8a00bc61

## Parking UUIDs
```
PLACE_ID=7e9536c2-08d1-4fdc-b1be-e53cdcc82149
TOKEN=...
DATE_TIME=20/04/2026;08:00;08:01

curl --get \
--data-urlencode "datetime=${DATE_TIME}" \
--data-urlencode "search=is_my_allocated:;sector_uuid:" \
--data-urlencode "type=parking" \
--data-urlencode "is_by_pass_restriction=false" \
--data-urlencode "is_by_pass_state=false" \
--data-urlencode "is_service_booking=false" \
-H "authorization: Bearer ${TOKEN}" \
"https://api.deskbee.io/api/plant/${PLACE_ID}/places" | \
jq -r '.data[] | "- \"\(.uuid)\" # \(.name)"'
```


Result:
- "b54a3c2f-d9d1-4220-8940-2ea10f17815e" # PS.LOD.-2.2.17
- "a796c9ec-d888-4692-b2c6-659a0485eaaa" # PS.LOD.-2.2.18
- "871fe8dc-9753-4260-901a-00219b83d5f6" # PS.LOD.-2.2.16
- "04563436-a221-4aeb-9079-c6e5cf3bf8b0" # PS.LOD.-2.2.31
- "cd494aa3-a1da-4f73-8451-0274b6d9d464" # PS.LOD.-2.2.30
- "6d1789cb-876b-4d25-a424-32dfa3cc139a" # PS.LOD.-2.2.32
- "8c5bcd24-eca9-48b1-9635-128c2a582987" # PS.LOD.-2.2.19
- "379a2937-062b-405e-b938-298929a4ac9c" # PS.LOD.-2.2.20
- "23bd7353-38f2-4d93-8550-c063208ef304" # PS.LOD.-2.2.21
- "f0e44329-af9e-4c43-a048-a0f22e6a2eb5" # PS.LOD.-2.2.22
- "3918c2d7-6bbf-4fe0-aefe-ddc3b171c8da" # PS.LOD.-2.2.23
- "3fff62df-511c-4fea-a428-daf482130b35" # PS.LOD.-2.2.24
- "a83153ac-c3f2-4b23-bd7f-8a6f52f3178a" # PS.LOD.-2.2.25
- "85f852bb-4d89-45af-a093-367e558ae01c" # PS.LOD.-2.2.26
- "c8d3a5ee-e4b3-4808-878b-2e3231a32e65" # PS.LOD.-2.2.36
- "a5d87e8c-77bb-4e2b-9b46-b142658983c9" # PS.LOD.-2.2.13
- "f75fe94d-e388-4aca-acc8-39e5edeba6da" # PS.LOD.-2.2.27
- "f8eebb71-6240-4e68-af64-2c61baf75c26" # PS.LOD.-2.2.29
- "7307aa35-e058-4f95-be16-a7644c25d15d" # PS.LOD.-2.2.70
- "b63d7c3b-f29b-4019-9d55-8fd1d2951bd6" # PS.LOD.-2.2.71
- "047f7421-0b48-4385-824b-e2511bb91f79" # PS.LOD.-2.2.72
- "9e20760d-19e5-46d1-aa90-4a26cbdc32ed" # PS.LOD.-2.2.73
- "a58bd321-7e73-4b60-a28b-ea45f3fcec50" # LOD.-2.2.74
- "816b5e2a-6a93-4ea1-9aa3-e6f2ae511fbe" # PS.LOD.-2.2.75
- "e381c51d-5735-4c07-af70-49646f8bfd3d" # PS.LOD.-2.2.76
- "c3e04e79-7c0d-461f-ba3b-1ffd8ca30ff3" # PS.LOD.-2.2.77
- "4c589cc2-9d23-4de8-baf6-3ee8677ec1b2" # PS.LOD.-2.2.78
- "d4559b32-fb3a-4568-a178-e26f0d1b5c7c" # PS.LOD.-2.2.79
- "32a6c690-ffbe-42cc-a6c8-de31b6b99367" # PS.LOD.-2.2.80
- "13e77878-d001-41d3-9ce8-813c6b086e9d" # PS.LOD.-2.2.81
- "e7327d90-4dbf-495b-902d-812bb4a005c1" # PS.LOD.-2.2.82
- "a0517848-c5fe-4ca3-9b58-c03cdf09d354" # PS.LOD.-2.2.83
- "a4a926d4-ca11-496f-9ea7-ed5dc4769b1c" # PS.LOD.-2.2.84
- "42674a0c-1def-437a-b66a-5d8e826e1518" # PS.LOD.-2.2.85
- "690fb076-2eea-490d-b929-02f099f0b99c" # PS.LOD.-2.2.86
- "43c5fc02-c772-40fa-8e18-67fef5a51b5b" # PS.LOD.-2.2.87
- "15211ad9-20a1-4940-94bf-7340d2826f9c" # PS.LOD.-2.2.88
- "329847f6-0fd7-403c-bf7c-a4663bde635a" # PS.LOD.-2.2.89
- "a5270721-0407-46f5-b192-65ad73905012" # PS.LOD.-2/2.28
- "7d95c4ff-78cb-44ee-b7af-bd165f21f05b" # PS.LOD.-2.2.15

b54a3c2f-d9d1-4220-8940-2ea10f17815e,a796c9ec-d888-4692-b2c6-659a0485eaaa,871fe8dc-9753-4260-901a-00219b83d5f6,04563436-a221-4aeb-9079-c6e5cf3bf8b0,cd494aa3-a1da-4f73-8451-0274b6d9d464,6d1789cb-876b-4d25-a424-32dfa3cc139a,8c5bcd24-eca9-48b1-9635-128c2a582987,379a2937-062b-405e-b938-298929a4ac9c,23bd7353-38f2-4d93-8550-c063208ef304,f0e44329-af9e-4c43-a048-a0f22e6a2eb5,3918c2d7-6bbf-4fe0-aefe-ddc3b171c8da,3fff62df-511c-4fea-a428-daf482130b35,a83153ac-c3f2-4b23-bd7f-8a6f52f3178a,85f852bb-4d89-45af-a093-367e558ae01c,c8d3a5ee-e4b3-4808-878b-2e3231a32e65,a5d87e8c-77bb-4e2b-9b46-b142658983c9,f75fe94d-e388-4aca-acc8-39e5edeba6da,f8eebb71-6240-4e68-af64-2c61baf75c26,7307aa35-e058-4f95-be16-a7644c25d15d,b63d7c3b-f29b-4019-9d55-8fd1d2951bd6,047f7421-0b48-4385-824b-e2511bb91f79,9e20760d-19e5-46d1-aa90-4a26cbdc32ed,a58bd321-7e73-4b60-a28b-ea45f3fcec50,816b5e2a-6a93-4ea1-9aa3-e6f2ae511fbe,e381c51d-5735-4c07-af70-49646f8bfd3d,c3e04e79-7c0d-461f-ba3b-1ffd8ca30ff3,4c589cc2-9d23-4de8-baf6-3ee8677ec1b2,d4559b32-fb3a-4568-a178-e26f0d1b5c7c,32a6c690-ffbe-42cc-a6c8-de31b6b99367,13e77878-d001-41d3-9ce8-813c6b086e9d,e7327d90-4dbf-495b-902d-812bb4a005c1,a0517848-c5fe-4ca3-9b58-c03cdf09d354,a4a926d4-ca11-496f-9ea7-ed5dc4769b1c,42674a0c-1def-437a-b66a-5d8e826e1518,690fb076-2eea-490d-b929-02f099f0b99c,43c5fc02-c772-40fa-8e18-67fef5a51b5b,15211ad9-20a1-4940-94bf-7340d2826f9c,329847f6-0fd7-403c-bf7c-a4663bde635a,a5270721-0407-46f5-b192-65ad73905012,7d95c4ff-78cb-44ee-b7af-bd165f21f05b