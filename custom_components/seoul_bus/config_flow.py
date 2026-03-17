import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers import selector
from .const import DOMAIN, CONF_STATION_ID, CONF_STATION_NAME, CONF_START_TIME, CONF_END_TIME, CONF_API_ISSUED_DATE

class SeoulBusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # unique_id 설정 및 중복 체크
            await self.async_set_unique_id(user_input[CONF_STATION_ID])
            self._abort_if_unique_id_configured()
            
            title = user_input.get(CONF_STATION_NAME) or f"정류장 {user_input[CONF_STATION_ID]}"
            return self.async_create_entry(title=title, data=user_input)

        # 400 에러 방지를 위해 스키마 구조를 최대한 단순화
        # TimeSelector의 default는 반드시 format과 글자수가 일치해야 함 (5자리)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_STATION_ID): str,
                vol.Optional(CONF_STATION_NAME): str,
                vol.Optional(CONF_START_TIME, default="00:00"): selector.TimeSelector(selector.TimeSelectorConfig(format="hh:mm")),
                vol.Optional(CONF_END_TIME, default="00:00"): selector.TimeSelector(selector.TimeSelectorConfig(format="hh:mm")),
                vol.Optional("include_buses"): str,
                vol.Optional(CONF_API_ISSUED_DATE): str,
            }),
            errors=errors,
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
        
        # 안전하게 데이터를 가져오기 위한 헬퍼 (기본값 최소화)
        def get_v(key, default_val=None):
            return options.get(key, data.get(key, default_val))

        # TimeSelector 값 정제 (8자리면 5자리로)
        def fix_t(val):
            t = get_v(val, "00:00")
            return t[:5] if t else "00:00"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY, default=get_v(CONF_API_KEY, "")): str,
                vol.Required(CONF_STATION_ID, default=get_v(CONF_STATION_ID, "")): str,
                vol.Optional(CONF_STATION_NAME, default=get_v(CONF_STATION_NAME, "")): str,
                vol.Optional(CONF_START_TIME, default=fix_t(CONF_START_TIME)): selector.TimeSelector(selector.TimeSelectorConfig(format="hh:mm")),
                vol.Optional(CONF_END_TIME, default=fix_t(CONF_END_TIME)): selector.TimeSelector(selector.TimeSelectorConfig(format="hh:mm")),
                vol.Optional("include_buses", default=get_v("include_buses", "")): str,
                vol.Optional(CONF_API_ISSUED_DATE, default=get_v(CONF_API_ISSUED_DATE, "")): str,
            }),
        )
