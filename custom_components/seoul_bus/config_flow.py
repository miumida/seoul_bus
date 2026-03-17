import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.helpers import selector
from .const import DOMAIN, CONF_STATION_ID, CONF_START_TIME, CONF_END_TIME, CONF_API_ISSUED_DATE, DEFAULT_NAME

class SeoulBusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_STATION_ID])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input.get(CONF_NAME, DEFAULT_NAME), data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                # API 키를 별표(****)로 숨김 처리
                vol.Required(CONF_API_KEY): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Required(CONF_STATION_ID): str,
                vol.Optional("include_buses", default=""): str,
                vol.Optional("exclude_buses", default=""): str,
                vol.Optional(CONF_API_ISSUED_DATE): str,
                vol.Optional(CONF_START_TIME, default="00:00"): str,
                vol.Optional(CONF_END_TIME, default="23:59"): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SeoulBusOptionsFlowHandler(config_entry)

class SeoulBusOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        # self.config_entry 필드 충돌 에러 수정을 위해 변수명 변경
        self._custom_config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self._custom_config_entry.options
        data = self._custom_config_entry.data
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY, default=options.get(CONF_API_KEY, data.get(CONF_API_KEY))): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Optional("include_buses", default=options.get("include_buses", data.get("include_buses", ""))): str,
                vol.Optional("exclude_buses", default=options.get("exclude_buses", data.get("exclude_buses", ""))): str,
                vol.Optional(CONF_API_ISSUED_DATE, default=options.get(CONF_API_ISSUED_DATE, data.get(CONF_API_ISSUED_DATE, ""))): str,
                vol.Required(CONF_START_TIME, default=options.get(CONF_START_TIME, data.get(CONF_START_TIME, "00:00"))): str,
                vol.Required(CONF_END_TIME, default=options.get(CONF_END_TIME, data.get(CONF_END_TIME, "23:59"))): str,
            }),
        )
