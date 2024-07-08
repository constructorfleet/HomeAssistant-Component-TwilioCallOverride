from typing import List, Dict, Any, Optional, Tuple
import re
import logging

import voluptuous as vol
from homeassistant.components.notify.const import ATTR_DATA, ATTR_TARGET
from homeassistant.core import Context
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import intent

from .const import (
    DOMAIN,
    ATTR_STATUS_WEBHOOK,
    ATTR_CALL_SID_EVENT,
    DEFAULT_CALL_SID_EVENT
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(ATTR_STATUS_WEBHOOK, default=None): cv.url,
        vol.Required(ATTR_CALL_SID_EVENT, default=DEFAULT_CALL_SID_EVENT): cv.slugify,
    })
}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass, config):
    """Set up the twilio_call_override component."""

    from homeassistant.components.twilio_call.notify import TwilioCallNotificationService

    original = TwilioCallNotificationService.send_message
    webhook_url = config.get(ATTR_STATUS_WEBHOOK, None)
    call_sid_event = config.get(ATTR_CALL_SID_EVENT, DEFAULT_CALL_SID_EVENT)

    def send_message(self, message="", **kwargs):
        """Call to specified target users."""
        if not (targets := kwargs.get(ATTR_TARGET)):
            _LOGGER.info("At least 1 target is required")
            return

        if message.startswith(("http://", "https://")):
            twimlet_url = message
        else:
            twimlet_url = "http://twimlets.com/message?Message="
            twimlet_url += urllib.parse.quote(message, safe="")
        
        if kwargs.get(ATTR_DATA, None) is not None and kwargs[ATTR_DATA].get(ATTR_STATUS_WEBHOOK, None) is not None:
            status_callback = kwargs[ATTR_DATA][ATTR_STATUS_WEBHOOK]
            status_callback_method = "POST"
        elif webhook_url is not None:
            status_callback = webhook_url
            status_callback_method = "POST"
        else:
            status_callback = None
            status_callback_method = None

        for target in targets:
            try:
                call = self.client.calls.create(
                    to=target, url=twimlet_url, from_=self.from_number,
                    status_callback=status_callback, status_callback_method=status_callback_method
                )
                self.hass.bus.async_fire(call_sid_event, {
                    "call_sid": call.sid,
                    "date_created": call.date_created,
                    "to": call.to,
                    "to_formatted": call.to_formatted,
                    "from": call._from,
                    "from_formatted": call.from_formatted,
                })
            except TwilioRestException as exc:
                _LOGGER.error(exc)


    TwilioCallNotificationService.send_message = send_message

    return True
