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
            # 중복 체크
            await self.async_set_unique_id(user_input[CONF_STATION_ID])
            self._abort_if_unique_id_configured()
            
            title = user_input.get(CONF_STATION_NAME) or f"정류장 {user_input[CONF_STATION_ID]}"
            return self.async_create_entry(title=title, data=user_input)

        # 400 에러를 방지하기 위한 가장 깨끗한 스키마
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_STATION_ID): str,
                vol.Optional(CONF_STATION_NAME): str,
                # 'hh:mm' 포맷을 명시하고 기본값에서도 초 단위를 완전히 제거
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
        
        # 시간값 정규화: 기존에 00:00:00으로 저장되어 있었다면 앞 5자리(HH:MM)만 추출
        def get_clean_time(key):
            val = options.get(key, data.get(key, "00:00"))
            return val[:5] if val else "00:00"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY, default=options.get(CONF_API_KEY, data.get(CONF_API_KEY, ""))): str,
                vol.Required(CONF_STATION_ID, default=options.get(CONF_STATION_ID, data.get(CONF_STATION_ID, ""))): str,
                vol.Optional(CONF_STATION_NAME, default=options.get(CONF_STATION_NAME, data.get(CONF_STATION_NAME, ""))): str,
                vol.Optional(CONF_START_TIME, default=get_clean_time(CONF_START_TIME)): selector.TimeSelector(
                    selector.TimeSelectorConfig(format="hh:mm")
                ),
                vol.Optional(CONF_END_TIME, default=get_clean_time(CONF_END_TIME)): selector.TimeSelector(
                    selector.TimeSelectorConfig(format="hh:mm")
                ),
                vol.Optional("include_buses", default=options.get("include_buses", data.get("include_buses", ""))): str,
                vol.Optional(CONF_API_ISSUED_DATE, default=options.get(CONF_API_ISSUED_DATE, data.get(CONF_API_ISSUED_DATE, ""))): str,
            }),
        )
