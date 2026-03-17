from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CONF_STATION_ID, CONF_API_ISSUED_DATE, CONF_STATION_NAME

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    conf = {**entry.data, **entry.options}
    station_id = conf.get(CONF_STATION_ID)
    station_nm = conf.get(CONF_STATION_NAME) or f"정류장 {station_id}"
    include_list = [x.strip() for x in conf.get("include_buses", "").split(",") if x.strip()]

    entities = []
    
    issued_date = conf.get(CONF_API_ISSUED_DATE)
    if issued_date:
        entities.append(SeoulBusApiInfoSensor(issued_date, entry))

    # 정류장 상태 센서
    entities.append(SeoulBusStationSensor(coordinator, station_id, station_nm, entry))

    # 버스 노선 센서 (데이터가 없어도 엔티티 생성을 유지하여 '사용불가' 방지)
    data_struct = coordinator.data if isinstance(coordinator.data, dict) else {}
    items = data_struct.get("items", [])
    
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
        # [핵심] 모든 인스턴스를 하나의 고유 ID로 묶어 기기를 하나로 합침
        return {
            "identifiers": {(DOMAIN, "seoul_bus_global_integrated_device")},
            "name": "서울 버스 통합 정보",
            "manufacturer": "Seoul Bus API",
            "model": "통합 관리 서비스",
        }

class SeoulBusApiInfoSensor(SeoulBusBaseEntity, SensorEntity):
    def __init__(self, issued_date, entry):
        super().__init__(entry)
        self._issued_date = issued_date
        self._attr_unique_id = f"seoul_bus_api_info_{entry.entry_id}"
        self._attr_name = "API 만료 정보"
        self._attr_icon = "mdi:key-variant"

    @property
    def state(self):
        try:
            tmp = self._issued_date.split("-")
            expired = datetime(year=int(tmp[0])+2, month=int(tmp[1]), day=int(tmp[2]))
            return (expired - datetime.today()).days
        except: return "오류"

class SeoulBusStationSensor(CoordinatorEntity, SeoulBusBaseEntity, SensorEntity):
    def __init__(self, coordinator, station_id, station_name, entry):
        super().__init__(coordinator)
        SeoulBusBaseEntity.__init__(self, entry)
        self._attr_unique_id = f"seoul_bus_{station_id}"
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

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data if isinstance(self.coordinator.data, dict) else {}
        items = data.get("items", [])
        for item in items:
            if item.get('busRouteId') == self._route_id:
                return {"방향": item.get('adirection'), "두번째도착": item.get('arrmsg2'), "정류소ID": self._station_id}
        return {}
