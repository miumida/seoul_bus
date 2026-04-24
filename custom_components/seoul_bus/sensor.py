import logging
import re
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import slugify
from homeassistant.util import dt as dt_util
from .const import DOMAIN, VERSION, CONF_STATION_ID, CONF_STATION_NAME, CONF_INCLUDE_BUSES, CONF_TIME_OFFSET

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    station_id = entry.data[CONF_STATION_ID]
    station_name = entry.data.get(CONF_STATION_NAME) or f"정류장 {station_id}"
    
    include_str = entry.options.get(CONF_INCLUDE_BUSES, entry.data.get(CONF_INCLUDE_BUSES, ""))
    include_targets = [x.strip() for x in include_str.split(",")] if include_str else []
    
    current_unique_ids = []
    ent_reg = er.async_get(hass) # 엔티티 레지스트리 객체
    
    status_id = f"{DOMAIN}_{station_id}_status_sensor"
    update_id = f"{DOMAIN}_{station_id}_last_update_sensor"
    current_unique_ids.extend([status_id, update_id])
    
    entities = [
        SeoulBusStationSensor(coordinator, entry, station_id, station_name, status_id),
        SeoulBusLastUpdateSensor(coordinator, entry, station_id, station_name, update_id)
    ]
    
    added_bus_ids = set()

    def add_bus_entities(item, bus_route_id, base_unique_id, last_known_nm=None):
        time_uid = f"{base_unique_id}_time"
        timestamp_uid = f"{base_unique_id}_timestamp"
        stations_uid = f"{base_unique_id}_stations"
        
        entities.append(SeoulBusTimeSensor(coordinator, entry, item, station_id, station_name, time_uid, bus_route_id, last_known_nm))
        entities.append(SeoulBusTimestampSensor(coordinator, entry, item, station_id, station_name, timestamp_uid, bus_route_id, last_known_nm))
        entities.append(SeoulBusStationsSensor(coordinator, entry, item, station_id, station_name, stations_uid, bus_route_id, last_known_nm))
        
        current_unique_ids.extend([time_uid, timestamp_uid, stations_uid])

    # 버스 센서 생성 로직
    for bus_id in include_targets:
        bus_unique_id = f"{DOMAIN}_{station_id}_{bus_id}_bus_sensor"
        if bus_unique_id not in added_bus_ids:
            target_entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, f"{bus_unique_id}_time")
            last_known_nm = None
            if target_entity_id:
                existing_entry = ent_reg.async_get(target_entity_id)
                if existing_entry and existing_entry.original_name:
                    last_known_nm = existing_entry.original_name.split(" (")[0]

            add_bus_entities(None, bus_id, bus_unique_id, last_known_nm)
            added_bus_ids.add(bus_unique_id)

    if not include_targets and coordinator.data and "items" in coordinator.data:
        for item in coordinator.data["items"]:
            bus_route_id = item.get("busRouteId")
            bus_unique_id = f"{DOMAIN}_{station_id}_{bus_route_id}_bus_sensor"
            if bus_unique_id not in added_bus_ids:
                add_bus_entities(item, bus_route_id, bus_unique_id)
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
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._station_id)},
            name=self._station_name,
            manufacturer="Seoul Bus",
            sw_version=VERSION,
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

    @property
    def icon(self):
        return "mdi:bus-stop"

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

    @property
    def icon(self):
        return "mdi:update"

class SeoulBusBusBaseSensor(SeoulBusBase, SensorEntity):
    def __init__(self, coordinator, entry, item, station_id, station_name, unique_id, bus_route_id, suffix, last_known_nm=None):
        super().__init__(coordinator, entry, station_id, station_name)
        self._bus_route_id = bus_route_id
        self._rt_nm = (item.get("rtNm") if item else None) or last_known_nm
        self.entity_id = f"sensor.{DOMAIN}_{slugify(station_id)}_{slugify(self._bus_route_id)}_{suffix}"
        self._attr_unique_id = unique_id

    def _update_rt_nm(self):
        items = self.coordinator.data.get("items", [])
        for item in items:
            if item.get("busRouteId") == self._bus_route_id:
                new_rt_nm = item.get("rtNm")
                if new_rt_nm:
                    self._rt_nm = new_rt_nm
                return item
        return None

    @property
    def _display_nm(self):
        return self._rt_nm if self._rt_nm else self._bus_route_id

class SeoulBusTimeSensor(SeoulBusBusBaseSensor):
    def __init__(self, coordinator, entry, item, station_id, station_name, unique_id, bus_route_id, last_known_nm=None):
        super().__init__(coordinator, entry, item, station_id, station_name, unique_id, bus_route_id, "time", last_known_nm)
        self._attr_native_unit_of_measurement = "min"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:timer-outline"

    @property
    def name(self):
        self._update_rt_nm()
        return f"{self._display_nm} 남은 시간 ({self._station_name})"

    @property
    def native_value(self):
        if self.coordinator.data.get("status") == "waiting":
            return None
        item = self._update_rt_nm()
        if not item: return None
        
        offset = self._entry.options.get(CONF_TIME_OFFSET, self._entry.data.get(CONF_TIME_OFFSET, 1))
        
        traTime1 = item.get("traTime1")
        if traTime1 and traTime1.isdigit():
            sec = int(traTime1)
            minutes = max(0, (sec // 60) - offset)
            return minutes
            
        return None

class SeoulBusTimestampSensor(SeoulBusBusBaseSensor):
    def __init__(self, coordinator, entry, item, station_id, station_name, unique_id, bus_route_id, last_known_nm=None):
        super().__init__(coordinator, entry, item, station_id, station_name, unique_id, bus_route_id, "timestamp", last_known_nm)
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = "mdi:clock-outline"

    @property
    def name(self):
        self._update_rt_nm()
        return f"{self._display_nm} 도착 예정 ({self._station_name})"

    @property
    def native_value(self):
        if self.coordinator.data.get("status") == "waiting":
            return None
        item = self._update_rt_nm()
        if not item: return None
        
        offset = self._entry.options.get(CONF_TIME_OFFSET, self._entry.data.get(CONF_TIME_OFFSET, 1))
        traTime1 = item.get("traTime1")
        
        if traTime1 and traTime1.isdigit():
            sec = int(traTime1)
            # Offset subtraction
            adjusted_sec = max(0, sec - (offset * 60))
            return dt_util.now() + timedelta(seconds=adjusted_sec)
            
        return None

class SeoulBusStationsSensor(SeoulBusBusBaseSensor):
    def __init__(self, coordinator, entry, item, station_id, station_name, unique_id, bus_route_id, last_known_nm=None):
        super().__init__(coordinator, entry, item, station_id, station_name, unique_id, bus_route_id, "stations", last_known_nm)
        self._attr_native_unit_of_measurement = "정류장"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:bus-marker"

    @property
    def name(self):
        self._update_rt_nm()
        return f"{self._display_nm} 남은 정류장 ({self._station_name})"

    @property
    def native_value(self):
        if self.coordinator.data.get("status") == "waiting":
            return None
        item = self._update_rt_nm()
        if not item: return None
        
        # arrmsg1 텍스트에서 [X번째 전] 추출
        arrmsg1 = item.get("arrmsg1", "")
        match = re.search(r'\[(\d+)번째 전\]', arrmsg1)
        if match:
            return int(match.group(1))
            
        # arrmsg1이 "곧 도착"이거나 정류장 수를 포함하지 않을 때
        # sectOrd1 같은 다른 필드가 있을 수도 있으나, arrmsg1에 없다면 0이나 1로 처리
        if "곧 도착" in arrmsg1:
            return 1 # 곧 도착은 보통 1번째 전
            
        return None

