import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import slugify
from .const import DOMAIN, CONF_STATION_ID, CONF_STATION_NAME

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    station_id = entry.data[CONF_STATION_ID]
    station_name = entry.data.get(CONF_STATION_NAME) or f"정류장 {station_id}"
    
    # 1. 현재 유효한 엔티티들의 unique_id 리스트 생성
    current_unique_ids = []
    
    # 기본 센서들 (상태, 업데이트 시간)
    status_id = f"{DOMAIN}_{station_id}_status_sensor"
    update_id = f"{DOMAIN}_{station_id}_last_update_sensor"
    current_unique_ids.extend([status_id, update_id])
    
    entities = [
        SeoulBusStationSensor(coordinator, entry, station_id, station_name, status_id),
        SeoulBusLastUpdateSensor(coordinator, entry, station_id, station_name, update_id)
    ]
    
    # 버스 센서들
    if coordinator.data and "items" in coordinator.data:
        for item in coordinator.data["items"]:
            bus_route_id = item.get("busRouteId")
            bus_unique_id = f"{DOMAIN}_{station_id}_{bus_route_id}_bus_sensor"
            current_unique_ids.append(bus_unique_id)
            entities.append(SeoulBusSensor(coordinator, entry, item, station_id, station_name, bus_unique_id))
            
    # 2. [핵심] 엔티티 레지스트리에서 더 이상 유효하지 않은 엔티티 삭제
    ent_reg = er.async_get(hass)
    # 현재 이 통합구성요소(config_entry)에 속한 모든 등록된 엔티티 확인
    registered_entities = er.async_entries_for_config_entry(ent_reg, entry.entry_id)
    
    for entity_entry in registered_entities:
        if entity_entry.unique_id not in current_unique_ids:
            _LOGGER.info("더 이상 필요 없는 서울 버스 센서 삭제: %s", entity_entry.entity_id)
            ent_reg.async_remove(entity_entry.entity_id)

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
    def __init__(self, coordinator, entry, station_id, station_name, unique_id):
        super().__init__(coordinator, entry, station_id, station_name)
        self.entity_id = f"sensor.{DOMAIN}_{slugify(station_id)}"
        self._attr_unique_id = unique_id
        self._attr_name = f"{station_name} 상태"

    @property
    def state(self):
        status = self.coordinator.data.get("status")
        return "운영중" if status == "active" else "업데이트 대기중"

class SeoulBusLastUpdateSensor(SeoulBusBase, SensorEntity):
    def __init__(self, coordinator, entry, station_id, station_name, unique_id):
        super().__init__(coordinator, entry, station_id, station_name)
        self.entity_id = f"sensor.{DOMAIN}_{slugify(station_id)}_last_update"
        self._attr_unique_id = unique_id
        self._attr_name = f"{station_name} 마지막 업데이트"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        return getattr(self.coordinator, "last_update_success_time", None)

class SeoulBusSensor(SeoulBusBase, SensorEntity):
    def __init__(self, coordinator, entry, item, station_id, station_name, unique_id):
        super().__init__(coordinator, entry, station_id, station_name)
        bus_route_id = item.get("busRouteId")
        bus_nm = item.get("rtNm")
        
        self.entity_id = f"sensor.{DOMAIN}_{slugify(station_id)}_{slugify(bus_route_id)}"
        self._attr_unique_id = unique_id
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
