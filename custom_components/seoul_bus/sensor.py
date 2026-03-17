from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CONF_STATION_ID, CONF_API_ISSUED_DATE, CONF_STATION_NAME

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    conf = {**entry.data, **entry.options}
    station_id = conf.get(CONF_STATION_ID)
    station_name = conf.get(CONF_STATION_NAME, "서울 버스")
    include_list = [x.strip() for x in conf.get("include_buses", "").split(",") if x.strip()]

    entities = []
    
    issued_date = conf.get(CONF_API_ISSUED_DATE)
    if issued_date:
        entities.append(SeoulBusApiInfoSensor(issued_date, entry.entry_id))

    # 정류장 상태 센서
    entities.append(SeoulBusStationSensor(coordinator, station_id, station_name))

    data = coordinator.data if isinstance(coordinator.data, list) else []
    if data:
        for item in data:
            bus_id = item.get('busRouteId')
            if bus_id:
                if include_list and bus_id not in include_list:
                    continue
                entities.append(SeoulBusSensor(coordinator, item, station_id))
    
    async_add_entities(entities)

class SeoulBusBaseEntity:
    @property
    def device_info(self):
        # 모든 센서를 하나의 통합 기기로 묶음
        return {
            "identifiers": {(DOMAIN, "integrated_seoul_bus_info")},
            "name": "서울 버스 통합 정보",
            "manufacturer": "Seoul Bus API",
            "model": "통합 관리 기기",
        }

class SeoulBusApiInfoSensor(SeoulBusBaseEntity, SensorEntity):
    def __init__(self, issued_date, entry_id):
        self._issued_date = issued_date
        self._attr_unique_id = f"seoul_bus_api_info_{entry_id}"
        self._attr_name = "API 만료 정보"
        self._attr_icon = "mdi:key-variant"

    @property
    def state(self):
        try:
            tmp = self._issued_date.split("-")
            expired = datetime(year=int(tmp[0])+2, month=int(tmp[1]), day=int(tmp[2]))
            return (expired - datetime.today()).days
        except: return "형식 오류"

    @property
    def unit_of_measurement(self): return "일"

class SeoulBusStationSensor(CoordinatorEntity, SeoulBusBaseEntity, SensorEntity):
    def __init__(self, coordinator, station_id, station_name):
        super().__init__(coordinator)
        self._station_id = station_id
        # 요청사항: 유니크 ID는 seoul_bus_station_id
        self._attr_unique_id = f"seoul_bus_{station_id}"
        self._attr_name = f"{station_name} 상태 ({station_id})"
        self._attr_icon = "mdi:nature-people"

    @property
    def state(self):
        if isinstance(self.coordinator.data, dict) and self.coordinator.data.get("status") == "waiting":
            return "업데이트 대기 중"
        if not self.coordinator.data:
            return "정보 없음"
        return "운행중" if any(i.get('vehId1', '0') != '0' for i in self.coordinator.data if isinstance(i, dict)) else "운행종료"

class SeoulBusSensor(CoordinatorEntity, SeoulBusBaseEntity, SensorEntity):
    def __init__(self, coordinator, item, station_id):
        super().__init__(coordinator)
        self._route_id = item.get('busRouteId')
        self._route_nm = item.get('rtNm', 'Unknown')
        self._station_id = station_id
        # 요청사항: 유니크 ID는 seoul_bus_station_id_bus_id
        self._attr_unique_id = f"seoul_bus_{station_id}_{self._route_id}"
        self._attr_name = f"{self._route_nm} 버스 ({station_id})"
        self._attr_icon = "mdi:bus"

    @property
    def state(self):
        if isinstance(self.coordinator.data, dict) and self.coordinator.data.get("status") == "waiting":
            return "업데이트 대기 중"
            
        if not isinstance(self.coordinator.data, list):
            return "정보 없음"

        for item in self.coordinator.data:
            if item.get('busRouteId') == self._route_id:
                return item.get('arrmsg1', '정보 없음')
        return "정보 없음"

    @property
    def extra_state_attributes(self):
        if not isinstance(self.coordinator.data, list): return {}
        for item in self.coordinator.data:
            if item.get('busRouteId') == self._route_id:
                return {
                    "방향": item.get('adirection'),
                    "두번째도착": item.get('arrmsg2'),
                    "정류소": item.get('stNm'),
                    "정류소ID": self._station_id
                }
        return {}
