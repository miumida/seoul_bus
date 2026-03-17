from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import slugify, dt as dt_util
from .const import DOMAIN, CONF_STATION_ID, CONF_STATION_NAME

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    station_id = entry.data[CONF_STATION_ID]
    station_name = entry.data.get(CONF_STATION_NAME) or f"정류장 {station_id}"
    
    # 1. 정류소 상태 센서
    entities = [SeoulBusStationSensor(coordinator, entry, station_id, station_name)]
    
    # 2. 마지막 업데이트 시간 센서
    entities.append(SeoulBusLastUpdateSensor(coordinator, entry, station_id, station_name))
    
    # 3. 개별 버스 센서
    if coordinator.data and "items" in coordinator.data:
        for item in coordinator.data["items"]:
            entities.append(SeoulBusSensor(coordinator, entry, item, station_id, station_name))
            
    async_add_entities(entities)

class SeoulBusBase(CoordinatorEntity):
    def __init__(self, coordinator, entry, station_id, station_name):
        super().__init__(coordinator)
        self._station_id = station_id
        self._station_name = station_name

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._station_id)},
            name=self._station_name,
            manufacturer="Seoul Bus",
            model="Bus Stop Info",
        )

class SeoulBusStationSensor(SeoulBusBase, SensorEntity):
    def __init__(self, coordinator, entry, station_id, station_name):
        super().__init__(coordinator, entry, station_id, station_name)
        # 요구사항 1.1: sensor.seoul_bus_07267
        self.entity_id = f"sensor.{DOMAIN}_{slugify(station_id)}"
        self._attr_unique_id = f"{DOMAIN}_{station_id}_station_status"
        self._attr_name = f"{station_name} 상태"

    @property
    def state(self):
        status = self.coordinator.data.get("status")
        return "운영중" if status == "active" else "업데이트 대기중"

class SeoulBusLastUpdateSensor(SeoulBusBase, SensorEntity):
    """정보 갱신 시간을 표시하는 센서"""
    def __init__(self, coordinator, entry, station_id, station_name):
        super().__init__(coordinator, entry, station_id, station_name)
        self.entity_id = f"sensor.{DOMAIN}_{slugify(station_id)}_last_update"
        self._attr_unique_id = f"{DOMAIN}_{station_id}_last_update"
        self._attr_name = f"{station_name} 업데이트 시간"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def state(self):
        # 코디네이터가 마지막으로 성공적으로 업데이트된 시간을 반환
        return self.coordinator.last_update_success_time if self.coordinator.last_update_success_time else None

class SeoulBusSensor(SeoulBusBase, SensorEntity):
    def __init__(self, coordinator, entry, item, station_id, station_name):
        super().__init__(coordinator, entry, station_id, station_name)
        # bus_id는 사용자가 예시로 든 100100203(busRouteId)를 사용
        bus_route_id = item.get("busRouteId")
        bus_nm = item.get("rtNm")
        
        # 요구사항 1.2: sensor.seoul_bus_07267_100100203
        self.entity_id = f"sensor.{DOMAIN}_{slugify(station_id)}_{slugify(bus_route_id)}"
        self._attr_unique_id = f"{DOMAIN}_{station_id}_{bus_route_id}"
        self._attr_name = f"{bus_nm} ({station_name})"
        self._bus_route_id = bus_route_id

    @property
    def state(self):
        if self.coordinator.data.get("status") == "waiting":
            return "업데이트 대기중"
        
        for item in self.coordinator.data.get("items", []):
            if item.get("busRouteId") == self._bus_route_id:
                return item.get("arrmsg1")
        return "정보 없음"
