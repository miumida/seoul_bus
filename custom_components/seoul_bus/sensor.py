from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CONF_STATION_ID, CONF_API_ISSUED_DATE

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    conf = {**entry.data, **entry.options}
    station_id = conf.get(CONF_STATION_ID)
    include_list = [x.strip() for x in conf.get("include_buses", "").split(",") if x.strip()]

    entities = []
    
    issued_date = conf.get(CONF_API_ISSUED_DATE)
    if issued_date:
        entities.append(SeoulBusApiInfoSensor(issued_date, entry.entry_id))

    # 데이터 유무와 상관없이 기기 확인용으로 생성
    entities.append(SeoulBusStationSensor(coordinator, station_id))

    if coordinator.data:
        for item in coordinator.data:
            bus_id = item.get('busRouteId')
            if include_list and bus_id not in include_list:
                continue
            entities.append(SeoulBusSensor(coordinator, item, station_id))
    
    async_add_entities(entities)

class SeoulBusBaseEntity:
    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "integrated_seoul_bus_device")},
            "name": "서울 버스 통합 정보",
            "manufacturer": "Seoul Bus API",
            "model": "서울 버스 정보 통합 관리",
        }

class SeoulBusApiInfoSensor(SeoulBusBaseEntity, SensorEntity):
    def __init__(self, issued_date, entry_id):
        self._issued_date = issued_date
        self._attr_unique_id = f"api_info_{entry_id}"
        self._attr_name = "API 만료 정보"
        self._attr_icon = "mdi:key-variant"

    @property
    def state(self):
        try:
            tmp = self._issued_date.split("-")
            expired = datetime(year=int(tmp[0])+2, month=int(tmp[1]), day=int(tmp[2]))
            return (expired - datetime.today()).days
        except: return "Error"

    @property
    def unit_of_measurement(self): return "일"

class SeoulBusStationSensor(CoordinatorEntity, SeoulBusBaseEntity, SensorEntity):
    def __init__(self, coordinator, station_id):
        super().__init__(coordinator)
        self._station_id = station_id
        self._attr_unique_id = f"station_status_{station_id}"
        self._attr_name = f"정류장 상태 ({station_id})"
        self._attr_icon = "mdi:nature-people"

    @property
    def state(self):
        if not self.coordinator.data:
            return "운행 정지 (시간외)"
        return "운행중" if any(i.get('vehId1', '0') != '0' for i in self.coordinator.data) else "운행종료"

class SeoulBusSensor(CoordinatorEntity, SeoulBusBaseEntity, SensorEntity):
    def __init__(self, coordinator, item, station_id):
        super().__init__(coordinator)
        self._route_id = item['busRouteId']
        self._route_nm = item['rtNm']
        self._station_id = station_id
        self._attr_unique_id = f"{station_id}_{self._route_id}"
        self._attr_name = f"{self._route_nm} 버스 ({station_id})"
        self._attr_icon = "mdi:bus"

    @property
    def state(self):
        for item in self.coordinator.data:
            if item['busRouteId'] == self._route_id: return item['arrmsg1']
        return "정보 없음"

    @property
    def extra_state_attributes(self):
        for item in self.coordinator.data:
            if item['busRouteId'] == self._route_id:
                return {"방향": item.get('adirection'), "두번째도착": item.get('arrmsg2'), "정류소": item.get('stNm'), "정류소ID": self._station_id}
        return {}
