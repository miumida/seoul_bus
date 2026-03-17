from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CONF_STATION_ID, CONF_STATION_NAME

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    conf = {**entry.data, **entry.options}
    station_id = conf.get(CONF_STATION_ID)
    station_nm = conf.get(CONF_STATION_NAME) or f"정류장 {station_id}"
    include_list = [x.strip() for x in conf.get("include_buses", "").split(",") if x.strip()]

    entities = []
    
    # 정류장 상태 센서
    entities.append(SeoulBusStationSensor(coordinator, station_id, station_nm, entry))

    data_struct = coordinator.data if isinstance(coordinator.data, dict) else {}
    items = data_struct.get("items", [])

    # 버스 센서 생성 (사용불가 방지 로직)
    if include_list:
        for b_id in include_list:
            entities.append(SeoulBusSensor(coordinator, {"busRouteId": b_id, "rtNm": b_id}, station_id, entry))
    elif items:
        for item in items:
            entities.append(SeoulBusSensor(coordinator, item, station_id, entry))
    
    async_add_entities(entities)

class SeoulBusBaseEntity:
    def __init__(self, entry):
        self._entry = entry

    @property
    def device_info(self):
        # [핵심] identifiers를 고정하여 모든 설정 건을 하나의 기기로 강제 통합
        return {
            "identifiers": {(DOMAIN, "seoul_bus_global_integrated_device")},
            "name": "서울 버스 통합 정보",
            "manufacturer": "Seoul Bus API",
            "model": "통합 관리 서비스",
        }

class SeoulBusStationSensor(CoordinatorEntity, SeoulBusBaseEntity, SensorEntity):
    def __init__(self, coordinator, station_id, station_name, entry):
        super().__init__(coordinator)
        SeoulBusBaseEntity.__init__(self, entry)
        self._attr_unique_id = f"seoul_bus_status_{station_id}"
        self._attr_name = f"{station_name} 상태"
        self._attr_icon = "mdi:nature-people"

    @property
    def state(self):
        data = self.coordinator.data if isinstance(self.coordinator.data, dict) else {}
        if data.get("status") == "waiting": return "업데이트 대기 중"
        items = data.get("items", [])
        if not items: return "정보 없음"
        return "운행중" if any(i.get('vehId1', '0') != '0' for i in items if isinstance(i, dict)) else "운행종료"

class SeoulBusSensor(CoordinatorEntity, SeoulBusBaseEntity, SensorEntity):
    def __init__(self, coordinator, item, station_id, entry):
        super().__init__(coordinator)
        SeoulBusBaseEntity.__init__(self, entry)
        self._route_id = item.get('busRouteId')
        self._route_nm = item.get('rtNm', self._route_id)
        self._station_id = station_id
        self._attr_unique_id = f"seoul_bus_{station_id}_{self._route_id}"
        self._attr_name = f"{self._route_nm} 버스 ({station_id})"
        self._attr_icon = "mdi:bus"

    @property
    def state(self):
        data = self.coordinator.data if isinstance(self.coordinator.data, dict) else {}
        if data.get("status") == "waiting": return "업데이트 대기 중"
        items = data.get("items", [])
        for item in items:
            if item.get('busRouteId') == self._route_id:
                return item.get('arrmsg1', '정보 없음')
        return "정보 없음"
