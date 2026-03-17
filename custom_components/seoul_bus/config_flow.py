import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers import selector
from .const import DOMAIN, CONF_STATION_ID, CONF_STATION_NAME, CONF_START_TIME, CONF_END_TIME, CONF_API_ISSUED_DATE

class SeoulBusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_STATION_ID])
            self._abort_if_unique_id_configured()
            
            title = user_input.get(CONF_STATION_NAME) or f"정류장 {user_input[CONF_STATION_ID]}"
            return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_STATION_ID): str,
                vol.Optional(CONF_STATION_NAME): str,
                # 시/분만 입력받는 가장 안전한 방법
                vol.Optional(CONF_START_TIME, default="00:00"): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TIME)
                ),
                vol.Optional(CONF_END_TIME, default="00:00"): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TIME)
                ),
                vol.Optional("include_buses"): str,
                vol.Optional(CONF_API_ISSUED_DATE): str,
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SeoulBusOptionsFlowHandler(config_entry)

class SeoulBusOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        conf = {**self._config_entry.data, **self._config_entry.options}
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY, default=conf.get(CONF_API_KEY, "")): str,
                vol.Required(CONF_STATION_ID, default=conf.get(CONF_STATION_ID, "")): str,
                vol.Optional(CONF_STATION_NAME, default=conf.get(CONF_STATION_NAME, "")): str,
                vol.Optional(CONF_START_TIME, default=conf.get(CONF_START_TIME, "00:00")[:5]): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TIME)
                ),
                vol.Optional(CONF_END_TIME, default=conf.get(CONF_END_TIME, "00:00")[:5]): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TIME)
                ),
                vol.Optional("include_buses", default=conf.get("include_buses", "")): str,
                vol.Optional(CONF_API_ISSUED_DATE, default=conf.get(CONF_API_ISSUED_DATE, "")): str,
            }),
        )
