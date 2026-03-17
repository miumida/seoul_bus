from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, CONF_STATION_ID, CONF_STATION_NAME

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    station_id = entry.data[CONF_STATION_ID]
    station_name = entry.data.get(CONF_STATION_NAME) or f"정류장 {station_id}"
    
    # 1. 정류장 센서 추가
    entities = [SeoulBusStationSensor(coordinator, entry, station_id, station_name)]
    
    # 2. 개별 버스 센서 추가
    if coordinator.data and "items" in coordinator.data:
        for item in coordinator.data["items"]:
            entities.append(SeoulBusSensor(coordinator, entry, item, station_id, station_name))
            
    async_add_entities(entities)

class SeoulBusBaseEntity(CoordinatorEntity):
    """공통 기기 정보를 관리하는 베이스 클래스"""
    def __init__(self, coordinator, entry, station_id, station_name):
        super().__init__(coordinator)
        self._station_id = station_id
        self._station_name = station_name
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        # 모든 엔티티가 동일한 identifiers를 가져야 하나의 기기로 묶입니다.
        return DeviceInfo(
            identifiers={(DOMAIN, self._station_id)},
            name=self._station_name,
            manufacturer="Seoul Bus",
            model="Bus Stop Info",
            configuration_url="http://ws.bus.go.kr",
        )

class SeoulBusStationSensor(SeoulBusBaseEntity, SensorEntity):
    """정류장 상태 센서 (sensor.seoul_bus_[station_id])"""
    def __init__(self, coordinator, entry, station_id, station_name):
        super().__init__(coordinator, entry, station_id, station_name)
        # 요구사항 2: 유니크 ID 및 엔티티 ID 형식 지정
        self._attr_unique_id = f"{DOMAIN}_{station_id}_station"
        self.entity_id = f"sensor.{DOMAIN}_{station_id}"
        self._attr_name = f"{station_name} 상태"

    @property
    def state(self):
        return self.coordinator.data.get("status", "unknown")

class SeoulBusSensor(SeoulBusBaseEntity, SensorEntity):
    """개별 버스 도착 센서 (sensor.seoul_bus_[bus_id])"""
    def __init__(self, coordinator, entry, item, station_id, station_name):
        super().__init__(coordinator, entry, station_id, station_name)
        bus_id = item.get("rtNm") # 버스 번호(이름)
        # 요구사항 2: 버스 센서 유니크 ID 및 엔티티 ID
        self._attr_unique_id = f"{DOMAIN}_{station_id}_{bus_id}"
        self.entity_id = f"sensor.{DOMAIN}_{bus_id}"
        self._attr_name = f"{bus_id} ({station_name})"
        self._bus_id = bus_id

    @property
    def state(self):
        if not self.coordinator.data or "items" not in self.coordinator.data:
            return None
        for item in self.coordinator.data["items"]:
            if item.get("rtNm") == self._bus_id:
                return item.get("arrmsg1")
        return "정보 없음"

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data or "items" not in self.coordinator.data:
            return {}
        for item in self.coordinator.data["items"]:
            if item.get("rtNm") == self._bus_id:
                return item
        return {}
