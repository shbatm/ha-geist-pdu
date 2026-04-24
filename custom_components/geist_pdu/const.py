"""Constants for the Geist PDU integration."""
from datetime import timedelta
import logging

DOMAIN = "geist_pdu"
LOGGER = logging.getLogger(__package__)

SCAN_INTERVAL = timedelta(seconds=30)

CONF_URL = "url"
