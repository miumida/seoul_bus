from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import slugify
from .const import DOMAIN, CONF_STATION_ID, CONF_STATION_NAME

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    station_id = entry.data[CONF_STATION_ID]
    station_name = entry.data.get(CONF_STATION_NAME) or f"정류장 {station_id}"
    
    entities = [
        SeoulBusStationSensor(coordinator, entry, station_id, station_name),
        SeoulBusLastUpdateSensor(coordinator, entry, station_id, station_name)
    ]
    
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
        )

class SeoulBusStationSensor(SeoulBusBase, SensorEntity):
    def __init__(self, coordinator, entry, station_id, station_name):
        super().__init__(coordinator, entry, station_id, station_name)
        # 요구사항 1.1: sensor.seoul_bus_07267
        self.entity_id = f"sensor.{DOMAIN}_{slugify(station_id)}"
        self._attr_unique_id = f"{DOMAIN}_{station_id}_status"
        self._attr_name = f"{station_name} 상태"

    @property
    def state(self):
        status = self.coordinator.data.get("status")
        return "운영중" if status == "active" else "업데이트 대기중"

class SeoulBusLastUpdateSensor(SeoulBusBase, SensorEntity):
    def __init__(self, coordinator, entry, station_id, station_name):
        super().__init__(coordinator, entry, station_id, station_name)
        # sensor.seoul_bus_07267_last_update
        self.entity_id = f"sensor.{DOMAIN}_{slugify(station_id)}_last_update"
        self._attr_unique_id = f"{DOMAIN}_{station_id}_last_update"
        self._attr_name = f"{station_name} 마지막 업데이트"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        # __init__.py에서 추가한 변수 참조 (에러 해결)
        return getattr(self.coordinator, "last_update_success_time", None)

class SeoulBusSensor(SeoulBusBase, SensorEntity):
    def __init__(self, coordinator, entry, item, station_id, station_name):
        super().__init__(coordinator, entry, station_id, station_name)
        bus_route_id = item.get("busRouteId")
        bus_nm = item.get("rtNm")
        
        # 요구사항 1.2: sensor.seoul_bus_07267_100100203
        # slugify(station_id)를 앞에 붙여서 형식을 고정함
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
