import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import slugify
from .const import DOMAIN, CONF_STATION_ID, CONF_STATION_NAME, CONF_INCLUDE_BUSES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    station_id = entry.data[CONF_STATION_ID]
    station_name = entry.data.get(CONF_STATION_NAME) or f"정류장 {station_id}"
    
    # 설정된 버스 목록 파싱
    include_str = entry.options.get(CONF_INCLUDE_BUSES, entry.data.get(CONF_INCLUDE_BUSES, ""))
    include_targets = [x.strip() for x in include_str.split(",")] if include_str else []
    
    # 1. 유지해야 할 unique_id 리스트 초기화
    current_unique_ids = []
    
    # 기본 센서 (항상 유지)
    status_id = f"{DOMAIN}_{station_id}_status_sensor"
    update_id = f"{DOMAIN}_{station_id}_last_update_sensor"
    current_unique_ids.extend([status_id, update_id])
    
    entities = [
        SeoulBusStationSensor(coordinator, entry, station_id, station_name, status_id),
        SeoulBusLastUpdateSensor(coordinator, entry, station_id, station_name, update_id)
    ]
    
    # 2. 버스 센서 생성 로직 (설정 기반)
    # API 응답 유무와 상관없이 설정에 있는 버스는 엔티티로 등록하여 삭제를 방지함
    added_bus_ids = set()

    # 우선 설정(include_buses)에 있는 버스들부터 엔티티 생성 리스트에 추가
    for bus_id in include_targets:
        bus_unique_id = f"{DOMAIN}_{station_id}_{bus_id}_bus_sensor"
        if bus_unique_id not in added_bus_ids:
            # 설정 기반 생성 시에는 초기 item 정보가 없으므로 None 전달 가능하도록 처리
            entities.append(SeoulBusSensor(coordinator, entry, None, station_id, station_name, bus_unique_id, bus_id))
            current_unique_ids.append(bus_unique_id)
            added_bus_ids.add(bus_unique_id)

    # 설정이 비어있을 경우에만 API 응답에 있는 모든 버스를 추가 (기존 로직 유지)
    if not include_targets and coordinator.data and "items" in coordinator.data:
        for item in coordinator.data["items"]:
            bus_route_id = item.get("busRouteId")
            bus_unique_id = f"{DOMAIN}_{station_id}_{bus_route_id}_bus_sensor"
            if bus_unique_id not in added_bus_ids:
                entities.append(SeoulBusSensor(coordinator, entry, item, station_id, station_name, bus_unique_id, bus_route_id))
                current_unique_ids.append(bus_unique_id)
                added_bus_ids.add(bus_unique_id)

    # 3. 자동 삭제: 현재 유지 리스트(설정값 포함)에 없는 엔티티만 레지스트리에서 제거
    ent_reg = er.async_get(hass)
    registered_entities = er.async_entries_for_config_entry(ent_reg, entry.entry_id)
    
    for entity_entry in registered_entities:
        if entity_entry.unique_id not in current_unique_ids:
            _LOGGER.info("설정에서 제외된 서울 버스 센서 자동 삭제: %s", entity_entry.entity_id)
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
    def __init__(self, coordinator, entry, item, station_id, station_name, unique_id, bus_route_id):
        super().__init__(coordinator, entry, station_id, station_name)
        # item이 없을 경우를 대비해 bus_route_id를 직접 받음
        self._bus_route_id = bus_route_id
        self._bus_nm = item.get("rtNm") if item else bus_route_id
        
        self.entity_id = f"sensor.{DOMAIN}_{slugify(station_id)}_{slugify(self._bus_route_id)}"
        self._attr_unique_id = unique_id
        self._attr_name = f"{self._bus_nm} ({station_name})"

    @property
    def state(self):
        # 시간외 대기 상태 처리 (핵심)
        if self.coordinator.data.get("status") == "waiting":
            return "업데이트 대기중"
        
        items = self.coordinator.data.get("items", [])
        for item in items:
            if item.get("busRouteId") == self._bus_route_id:
                return item.get("arrmsg1")
        return "정보 없음"
