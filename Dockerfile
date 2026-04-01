FROM ghcr.io/home-assistant/home-assistant:stable

# On container start, copy the seed configuration into a fresh /config
# and then start Home Assistant using that directory.
COPY ./config/ /config/