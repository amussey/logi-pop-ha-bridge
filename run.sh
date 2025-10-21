#!/usr/bin/with-contenv bashio

echo "==============================="
echo "Starting Logi POP HA Bridge..."
echo "==============================="

bashio::log.info "Starting the Logi HA Bridge addon..."

# Read values from the addon configuration and export them as environment variables
# bashio::config reads from /data/options.json
bashio::log.warning "Loading configuration from options.json."
bashio::log.info "Loading configuration into environment..."

export TRIGGER_DEVICE_ADDRESS=$(bashio::config 'trigger_device_address')
export LOGITECH_MFG_ID=$(bashio::config 'logitech_mfg_id')
export MQTT_BROKER_ADDRESS=$(bashio::config 'mqtt_broker.address')
export MQTT_PORT=$(bashio::config 'mqtt_broker.port')
export MQTT_USERNAME=$(bashio::config 'mqtt_broker.username')
export MQTT_PASSWORD=$(bashio::config 'mqtt_broker.password')
export DEVICE_UNIQUE_ID=$(bashio::config 'device.unique_id')
export DEVICE_NAME=$(bashio::config 'device.name')
export ACTION_TOPIC="homeassistant/device_automation/${DEVICE_UNIQUE_ID}/action"
export CONFIG_TOPIC="homeassistant/device_automation/${DEVICE_UNIQUE_ID}/config"

bashio::log.info "Configuration loaded. Starting Python application."

python3 -u /app/logi_ha_bridge/runner.py
