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
                vol.Required(CONF_API_KEY): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
                vol.Required(CONF_STATION_ID): selector.TextSelector(),
                vol.Optional("include_buses", default=""): selector.TextSelector(),
                vol.Optional(CONF_API_ISSUED_DATE): selector.TextSelector(),
                # 초 단위를 제거한 시:분 선택기
                vol.Optional(CONF_START_TIME, default="00:00"): selector.TimeSelector(selector.TimeSelectorConfig(format="hh:mm")),
                vol.Optional(CONF_END_TIME, default="00:00"): selector.TimeSelector(selector.TimeSelectorConfig(format="hh:mm")),
                vol.Optional(CONF_STATION_NAME, default=""): selector.TextSelector(),
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

        options = self._config_entry.options
        data = self._config_entry.data
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY, default=options.get(CONF_API_KEY, data.get(CONF_API_KEY))): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
                vol.Required(CONF_STATION_ID, default=options.get(CONF_STATION_ID, data.get(CONF_STATION_ID))): selector.TextSelector(),
                vol.Optional("include_buses", default=options.get("include_buses", data.get("include_buses", ""))): selector.TextSelector(),
                vol.Optional(CONF_API_ISSUED_DATE, default=options.get(CONF_API_ISSUED_DATE, data.get(CONF_API_ISSUED_DATE, ""))): selector.TextSelector(),
                vol.Required(CONF_START_TIME, default=options.get(CONF_START_TIME, data.get(CONF_START_TIME, "00:00"))): selector.TimeSelector(selector.TimeSelectorConfig(format="hh:mm")),
                vol.Required(CONF_END_TIME, default=options.get(CONF_END_TIME, data.get(CONF_END_TIME, "00:00"))): selector.TimeSelector(selector.TimeSelectorConfig(format="hh:mm")),
            }),
        )
