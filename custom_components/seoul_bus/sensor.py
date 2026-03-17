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
    
    include_str = entry.options.get(CONF_INCLUDE_BUSES, entry.data.get(CONF_INCLUDE_BUSES, ""))
    include_targets = [x.strip() for x in include_str.split(",")] if include_str else []
    
    current_unique_ids = []
    ent_reg = er.async_get(hass) # 엔티티 레지스트리 가져오기
    
    status_id = f"{DOMAIN}_{station_id}_status_sensor"
    update_id = f"{DOMAIN}_{station_id}_last_update_sensor"
    current_unique_ids.extend([status_id, update_id])
    
    entities = [
        SeoulBusStationSensor(coordinator, entry, station_id, station_name, status_id),
        SeoulBusLastUpdateSensor(coordinator, entry, station_id, station_name, update_id)
    ]
    
    added_bus_ids = set()

    # 버스 센서 생성 로직
    for bus_id in include_targets:
        bus_unique_id = f"{DOMAIN}_{station_id}_{bus_id}_bus_sensor"
        if bus_unique_id not in added_bus_ids:
            # [핵심] 레지스트리에서 기존에 저장된 이름이 있는지 확인
            existing_entry = ent_reg.async_get_unique_id(bus_unique_id)
            last_known_nm = None
            if existing_entry and existing_entry.original_name:
                # "2230 (중랑구청)" 형태에서 "2230"만 추출 시도
                last_known_nm = existing_entry.original_name.split(" (")[0]

            entities.append(SeoulBusSensor(coordinator, entry, None, station_id, station_name, bus_unique_id, bus_id, last_known_nm))
            current_unique_ids.append(bus_unique_id)
            added_bus_ids.add(bus_unique_id)

    if not include_targets and coordinator.data and "items" in coordinator.data:
        for item in coordinator.data["items"]:
            bus_route_id = item.get("busRouteId")
            bus_unique_id = f"{DOMAIN}_{station_id}_{bus_route_id}_bus_sensor"
            if bus_unique_id not in added_bus_ids:
                entities.append(SeoulBusSensor(coordinator, entry, item, station_id, station_name, bus_unique_id, bus_route_id))
                current_unique_ids.append(bus_unique_id)
                added_bus_ids.add(bus_unique_id)

    # 불필요 엔티티 삭제
    registered_entities = er.async_entries_for_config_entry(ent_reg, entry.entry_id)
    for entity_entry in registered_entities:
        if entity_entry.unique_id not in current_unique_ids:
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
    def __init__(self, coordinator, entry, item, station_id, station_name, unique_id, bus_route_id, last_known_nm=None):
        super().__init__(coordinator, entry, station_id, station_name)
        self._bus_route_id = bus_route_id
        # 1. API 데이터가 있으면 rtNm 사용
        # 2. 없으면 레지스트리에서 불러온 이름 사용
        # 3. 둘 다 없으면 ID 사용
        self._rt_nm = (item.get("rtNm") if item else None) or last_known_nm
        
        self.entity_id = f"sensor.{DOMAIN}_{slugify(station_id)}_{slugify(self._bus_route_id)}"
        self._attr_unique_id = unique_id

    @property
    def name(self):
        # 실시간 데이터에서 노선명 업데이트 및 캐싱
        items = self.coordinator.data.get("items", [])
        for item in items:
            if item.get("busRouteId") == self._bus_route_id:
                new_rt_nm = item.get("rtNm")
                if new_rt_nm:
                    self._rt_nm = new_rt_nm
                    break
        
        display_nm = self._rt_nm if self._rt_nm else self._bus_route_id
        return f"{display_nm} ({self._station_name})"

    @property
    def state(self):
        if self.coordinator.data.get("status") == "waiting":
            return "업데이트 대기중"
        
        items = self.coordinator.data.get("items", [])
        for item in items:
            if item.get("busRouteId") == self._bus_route_id:
                return item.get("arrmsg1")
        return "정보 없음"
