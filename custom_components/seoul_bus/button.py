from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, CONF_STATION_ID, CONF_STATION_NAME

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    station_id = entry.data[CONF_STATION_ID]
    station_name = entry.data.get(CONF_STATION_NAME) or f"정류장 {station_id}"
    
    async_add_entities([SeoulBusRefreshButton(coordinator, station_id, station_name)])

class SeoulBusRefreshButton(ButtonEntity):
    def __init__(self, coordinator, station_id, station_name):
        self._coordinator = coordinator
        self._station_id = station_id
        self._station_name = station_name # 누락되었던 변수 추가
        self._attr_name = f"{station_name} 새로고침"
        self._attr_unique_id = f"{DOMAIN}_{station_id}_refresh_button_entity"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._station_id)},
            name=self._station_name,
        )

    async def async_press(self) -> None:
        """버튼을 누르면 즉시 API 호출"""
        await self._coordinator.async_request_refresh()
