import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv
from .const import DOMAIN, CONF_STATION_ID, CONF_STATION_NAME, CONF_START_TIME, CONF_END_TIME, CONF_API_ISSUED_DATE

# 공통 스키마 정의 (가장 엄격하고 안전한 형태)
def get_schema(defaults=None):
    if defaults is None:
        defaults = {}
    
    return vol.Schema({
        vol.Required(CONF_API_KEY, default=defaults.get(CONF_API_KEY, "")): str,
        vol.Required(CONF_STATION_ID, default=defaults.get(CONF_STATION_ID, "")): str,
        vol.Optional(CONF_STATION_NAME, default=defaults.get(CONF_STATION_NAME, "")): str,
        # 시간 선택기를 단순 텍스트로 받거나 가장 기본 포맷으로 설정
        vol.Optional(CONF_START_TIME, default=defaults.get(CONF_START_TIME, "00:00")): selector.TimeSelector(selector.TimeSelectorConfig(format="hh:mm")),
        vol.Optional(CONF_END_TIME, default=defaults.get(CONF_END_TIME, "00:00")): selector.TimeSelector(selector.TimeSelectorConfig(format="hh:mm")),
        vol.Optional("include_buses", default=defaults.get("include_buses", "")): str,
        vol.Optional(CONF_API_ISSUED_DATE, default=defaults.get(CONF_API_ISSUED_DATE, "")): str,
    })

class SeoulBusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                await self.async_set_unique_id(user_input[CONF_STATION_ID])
                self._abort_if_unique_id_configured()
                
                # 시간 형식 통일 (초 단위 추가)
                for key in [CONF_START_TIME, CONF_END_TIME]:
                    if user_input[key] and len(user_input[key]) == 5:
                        user_input[key] = f"{user_input[key]}:00"

                title = user_input.get(CONF_STATION_NAME) or f"정류장 {user_input[CONF_STATION_ID]}"
                return self.async_create_entry(title=title, data=user_input)
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=get_schema(),
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
            # 시간 형식 통일
            for key in [CONF_START_TIME, CONF_END_TIME]:
                if user_input[key] and len(user_input[key]) == 5:
                    user_input[key] = f"{user_input[key]}:00"
            return self.async_create_entry(title="", data=user_input)

        # 기존 설정값 불러오기
        conf = {**self._config_entry.data, **self._config_entry.options}
        
        # UI 표시용 시간 변환 (00:00:00 -> 00:00)
        for key in [CONF_START_TIME, CONF_END_TIME]:
            if conf.get(key) and len(conf[key]) > 5:
                conf[key] = conf[key][:5]

        return self.async_show_form(
            step_id="init",
            data_schema=get_schema(conf),
        )
