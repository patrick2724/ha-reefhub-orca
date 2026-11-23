"""Constants for reefhub ORCA."""
from datetime import timedelta

DOMAIN = "reefhub_orca"
MANUFACTURER = "reefhub"
SCAN_INTERVAL = timedelta(seconds=30)

PLATFORMS = ["switch", "number", "button", "sensor", "binary_sensor"]

SERVICE_SET_CHANNEL = "set_channel"
ATTR_CHANNEL = "channel"
ATTR_POINT_A = "point_a"
ATTR_POINT_B = "point_b"
ATTR_SPEED = "speed"
