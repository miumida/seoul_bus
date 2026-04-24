import logging
from datetime import datetime, timedelta
import xmltodict
import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.util import dt as dt_util
from .const import (
    DOMAIN, CONF_STATION_ID, CONF_START_TIME, CONF_END_TIME, CONF_INCLUDE_BUSES,
    CONF_INTERVAL_1_START, CONF_INTERVAL_1_END, CONF_INTERVAL_1_SEC,
    CONF_INTERVAL_2_START, CONF_INTERVAL_2_END, CONF_INTERVAL_2_SEC,
    CONF_INTERVAL_3_START, CONF_INTERVAL_3_END, CONF_INTERVAL_3_SEC
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR, Platform.BUTTON]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    async def async_update_data():
        conf = {**entry.data, **entry.options}
        now = datetime.now().strftime("%H:%M")
        start = conf.get(CONF_START_TIME, "00:00")
        end = conf.get(CONF_END_TIME, "00:00")

        # 2.1 & 2.2: 시간 범위 체크 (같으면 24시간 작동)
        is_waiting = False
        if start != end:
            if start < end:
                if not (start <= now <= end): is_waiting = True
            else: # 자정 포함
                if not (now >= start or now <= end): is_waiting = True

        if is_waiting:
            # 대기 중에는 기본 간격(60초) 유지
            if coordinator.update_interval != timedelta(seconds=60):
                coordinator.update_interval = timedelta(seconds=60)
            return {"status": "waiting", "items": coordinator.data.get("items", []) if coordinator.data else []}

        # 동적 업데이트 주기 (커스텀 1~3)
        new_interval = 60
        intervals = [
            (conf.get(CONF_INTERVAL_1_START, ""), conf.get(CONF_INTERVAL_1_END, ""), conf.get(CONF_INTERVAL_1_SEC, 10)),
            (conf.get(CONF_INTERVAL_2_START, ""), conf.get(CONF_INTERVAL_2_END, ""), conf.get(CONF_INTERVAL_2_SEC, 10)),
            (conf.get(CONF_INTERVAL_3_START, ""), conf.get(CONF_INTERVAL_3_END, ""), conf.get(CONF_INTERVAL_3_SEC, 10)),
        ]
        
        for c_start, c_end, c_sec in intervals:
            if c_start and c_end and c_start != c_end:
                if c_start < c_end:
                    if c_start <= now <= c_end:
                        new_interval = c_sec
                        break
                else:
                    if now >= c_start or now <= c_end:
                        new_interval = c_sec
                        break
                        
        if coordinator.update_interval != timedelta(seconds=new_interval):
            coordinator.update_interval = timedelta(seconds=new_interval)
            _LOGGER.debug(f"Update interval changed to {new_interval}s for {entry.data.get(CONF_STATION_ID)}")


        url = f"http://ws.bus.go.kr/api/rest/stationinfo/getStationByUid?ServiceKey={conf[CONF_API_KEY]}&arsId={conf[CONF_STATION_ID]}"
        try:
            async with async_timeout.timeout(15):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        res_text = await response.text()
                        data = xmltodict.parse(res_text)
                        items = data.get('ServiceResult', {}).get('msgBody', {}).get('itemList', [])
                        if not isinstance(items, list): items = [items] if items else []
                        
                        # 2.3: 버스 필터링
                        include_str = conf.get(CONF_INCLUDE_BUSES, "")
                        if include_str:
                            targets = [x.strip() for x in include_str.split(",")]
                            items = [i for i in items if i.get("rtNm") in targets or i.get("busRouteId") in targets]
                            
                        # 마지막 업데이트 시간 기록
                        coordinator.last_update_success_time = dt_util.now()
                        return {"status": "active", "items": items}
        except Exception as err:
            raise UpdateFailed(f"API Error: {err}")

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name=f"{DOMAIN}_{entry.data[CONF_STATION_ID]}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=60),
    )
    
    # 에러 방지용 초기값 설정
    coordinator.last_update_success_time = dt_util.now()

    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    entry.async_on_unload(entry.add_update_listener(lambda h, e: h.config_entries.async_reload(e.entry_id)))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
