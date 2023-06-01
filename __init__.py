from typing import List, Dict, Any, Optional, Tuple
import re
import logging

import voluptuous as vol
import homeassistant.components.conversation
from homeassistant.components import conversation
from homeassistant.core import Context
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import intent

from .const import (
    ATTR_RESPONSE_PARSER_START,
    ATTR_RESPONSE_PARSER_END,
    ATTR_FIRE_INTENT_NAME,
    DEFAULT_PARSER_TOKEN,
    DEFAULT_INTENT_NAME,
    DOMAIN
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(ATTR_RESPONSE_PARSER_START, default=DEFAULT_PARSER_TOKEN): cv.string,
        vol.Required(ATTR_RESPONSE_PARSER_END, default=DEFAULT_PARSER_TOKEN): cv.string,
        vol.Required(ATTR_FIRE_INTENT_NAME, default=DEFAULT_INTENT_NAME): cv.slugify
    })
}, extra=vol.ALLOW_EXTRA)


#
# class OpenAIIntentHandler(intent.IntentHandler):
#     """OpenAI Intent handler registration."""
#
#     # We use a small timeout in service calls to (hopefully) pass validation
#     # checks, but not try to wait for the call to fully complete.
#     service_timeout: float = 0.2
#
#     slot_schema = {
#         vol.Required("intentions"): vol.All(
#             cv.ensure_list,
#             [{
#                 vol.Required("message"): cv.string,
#                 vol.Optional("service_data"): cv.SERVICE_SCHEMA
#             }]
#         )
#     }
#
#     def __init__(
#             self, intent_type: str
#     ) -> None:
#         """Create OpenAI Intent Handler."""
#         self.intent_type = intent_type
#
#     async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
#         """Handle the hass intent."""
#         hass = intent_obj.hass
#         slots = self.async_validate_slots(intent_obj.slots)
#
#         success_results: list[intent.IntentResponseTarget] = []
#         failed_results: list[intent.IntentResponseTarget] = []
#         response = intent_obj.create_response()
#
#         for intention in slots.get("intentions", []):
#             if intention.get("service", None) is None:
#                 continue
#
#
#
#         return response
#
#     async def async_handle_intention(self, intent_obj: intent.Intent, intention: Dict[str, Any]) -> Tuple[bool, intent.IntentResponseTarget]:
#         """Handle intention."""
#         try:
#             await self.async_call_service(intent_obj, intention.get('service'))
#             return (True, intent.IntentResponseTarget(
#                 type=intent.IntentResponseTargetType.ENTITY,
#                 name=intention.get("service")
#
#             ))
#         except Exception:
#             return None
#
#     async def async_call_service(self, intent_obj: intent.Intent, service_intent: Dict[str, Any]) -> None:
#         """Call service on entity."""
#         hass = intent_obj.hass
#         service = service_intent.pop("service")
#         service_data = service_intent.pop("service_data")
#         await hass.services.async_call(
#             service.split(".")[0],
#             service.split(".")[1],
#             service_data,
#             context=intent_obj.context,
#             blocking=True,
#             limit=self.service_timeout,
#         )


async def async_setup(hass, config):
    """Set up the openai_override component."""
    conf = config[DOMAIN]
    start_token = conf[ATTR_RESPONSE_PARSER_START]
    service_regex = re.compile("({}.+?{})".format(conf[ATTR_RESPONSE_PARSER_START], conf[ATTR_RESPONSE_PARSER_END]))

    _LOGGER.info("Start token: {}".format(start_token))

    from homeassistant.components.openai_conversation import OpenAIAgent

    original = OpenAIAgent.async_process

    async def async_process(self, user_input: conversation.ConversationInput) -> conversation.ConversationResult:
        """Handle OpenAI intent."""
        result = await original(self, user_input)
        _LOGGER.info("Error code: {}".format(result.response.error_code))
        if result.response.error_code is not None:
            return result

        _LOGGER.info("Speech: {}".format(result.response.speech["plain"]["speech"]))

        segments = service_regex.split(result.response.speech["plain"]["speech"])
        content = ".  ".join([segment for segment in segments if start_token not in segment])

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(content)
        return conversation.ConversationResult(
            response=intent_response, conversation_id=result.conversation_id
        )

        result.response.async_set_speech(
            )

        return result

    OpenAIAgent.async_process = async_process

    return True
