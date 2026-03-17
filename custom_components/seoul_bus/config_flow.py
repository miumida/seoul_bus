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

        # 핵심: default와 format의 길이를 5자리로 통일
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_STATION_ID): str,
                vol.Optional(CONF_STATION_NAME): str,
                vol.Optional(CONF_START_TIME, default="00:00"): selector.TimeSelector(
                    selector.TimeSelectorConfig(format="hh:mm")
                ),
                vol.Optional(CONF_END_TIME, default="00:00"): selector.TimeSelector(
                    selector.TimeSelectorConfig(format="hh:mm")
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

        options = self._config_entry.options
        data = self._config_entry.data
        
        def get_v(key, default_val=""):
            return options.get(key, data.get(key, default_val))

        # 기존에 혹시라도 8자리로 저장된 데이터가 있다면 5자리로 잘라서 로드
        def fix_t(key):
            val = get_v(key, "00:00")
            return val[:5] if val else "00:00"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY, default=get_v(CONF_API_KEY)): str,
                vol.Required(CONF_STATION_ID, default=get_v(CONF_STATION_ID)): str,
                vol.Optional(CONF_STATION_NAME, default=get_v(CONF_STATION_NAME)): str,
                vol.Optional(CONF_START_TIME, default=fix_t(CONF_START_TIME)): selector.TimeSelector(
                    selector.TimeSelectorConfig(format="hh:mm")
                ),
                vol.Optional(CONF_END_TIME, default=fix_t(CONF_END_TIME)): selector.TimeSelector(
                    selector.TimeSelectorConfig(format="hh:mm")
                ),
                vol.Optional("include_buses", default=get_v("include_buses")): str,
                vol.Optional(CONF_API_ISSUED_DATE, default=get_v(CONF_API_ISSUED_DATE)): str,
            }),
        )
