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
            await self.async_set_unique_id(user_input[CONF_STATION_ID])
            self._abort_if_unique_id_configured()
            
            # 내부 연산을 위해 초 단위를 붙여야 한다면 여기서 변환
            for key in [CONF_START_TIME, CONF_END_TIME]:
                if len(user_input[key]) == 5: # "HH:MM" 형식인 경우
                    user_input[key] = f"{user_input[key]}:00"

            title = user_input.get(CONF_STATION_NAME) or f"정류장 {user_input[CONF_STATION_ID]}"
            return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
                vol.Required(CONF_STATION_ID): str,
                vol.Optional(CONF_STATION_NAME, default=""): str,
                # 기본값을 포맷과 동일하게 "00:00"으로 수정
                vol.Optional(CONF_START_TIME, default="00:00"): selector.TimeSelector(selector.TimeSelectorConfig(format="hh:mm")),
                vol.Optional(CONF_END_TIME, default="00:00"): selector.TimeSelector(selector.TimeSelectorConfig(format="hh:mm")),
                vol.Optional("include_buses", default=""): str,
                vol.Optional(CONF_API_ISSUED_DATE, default=""): str,
            }),
            errors=errors
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
            # 옵션 저장 시에도 시간 형식 보정
            for key in [CONF_START_TIME, CONF_END_TIME]:
                if len(user_input[key]) == 5:
                    user_input[key] = f"{user_input[key]}:00"
            return self.async_create_entry(title="", data=user_input)

        options = self._config_entry.options
        data = self._config_entry.data
        
        # 기존 저장된 데이터가 "00:00:00"인 경우 UI 로드를 위해 "00:00"으로 슬라이싱
        def format_time(val):
            return val[:5] if val and len(val) >= 5 else "00:00"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY, default=options.get(CONF_API_KEY, data.get(CONF_API_KEY))): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
                vol.Required(CONF_STATION_ID, default=options.get(CONF_STATION_ID, data.get(CONF_STATION_ID))): str,
                vol.Optional(CONF_STATION_NAME, default=options.get(CONF_STATION_NAME, data.get(CONF_STATION_NAME, ""))): str,
                vol.Required(CONF_START_TIME, default=format_time(options.get(CONF_START_TIME, data.get(CONF_START_TIME, "00:00")))): selector.TimeSelector(selector.TimeSelectorConfig(format="hh:mm")),
                vol.Required(CONF_END_TIME, default=format_time(options.get(CONF_END_TIME, data.get(CONF_END_TIME, "00:00")))): selector.TimeSelector(selector.TimeSelectorConfig(format="hh:mm")),
                vol.Optional("include_buses", default=options.get("include_buses", data.get("include_buses", ""))): str,
                vol.Optional(CONF_API_ISSUED_DATE, default=options.get(CONF_API_ISSUED_DATE, data.get(CONF_API_ISSUED_DATE, ""))): str,
            }),
        )
