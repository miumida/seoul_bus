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
from .const import DOMAIN, CONF_STATION_ID, CONF_START_TIME, CONF_END_TIME, CONF_INCLUDE_BUSES

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR, Platform.BUTTON]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    async def async_update_data():
        conf = {**entry.data, **entry.options}
        now = datetime.now().strftime("%H:%M")
        start = conf.get(CONF_START_TIME, "00:00")
        end = conf.get(CONF_END_TIME, "00:00")

        # 시간 범위 체크 (24시간 작동 또는 범위 내 작동)
        is_waiting = False
        if start != end:
            if start < end:
                if not (start <= now <= end): is_waiting = True
            else:
                if not (now >= start or now <= end): is_waiting = True

        if is_waiting:
            _LOGGER.debug("서울 버스: 현재 시간은 수집 제외 시간입니다.")
            return {"status": "waiting", "items": coordinator.data.get("items", []) if coordinator.data else []}

        url = f"http://ws.bus.go.kr/api/rest/stationinfo/getStationByUid?ServiceKey={conf[CONF_API_KEY]}&arsId={conf[CONF_STATION_ID]}"
        try:
            async with async_timeout.timeout(15):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        res_text = await response.text()
                        data = xmltodict.parse(res_text)
                        items = data.get('ServiceResult', {}).get('msgBody', {}).get('itemList', [])
                        if not isinstance(items, list): items = [items] if items else []
                        
                        include_str = conf.get(CONF_INCLUDE_BUSES, "")
                        if include_str:
                            targets = [x.strip() for x in include_str.split(",")]
                            items = [i for i in items if i.get("rtNm") in targets or i.get("busRouteId") in targets]
                        
                        # [핵심 수정] 성공 시 시간 기록
                        coordinator.last_update_success_time = dt_util.now()
                        return {"status": "active", "items": items}
        except Exception as err:
            raise UpdateFailed(f"API Error: {err}")

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name=f"{DOMAIN}_{entry.data[CONF_STATION_ID]}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=60),
    )
    # 초기화
    coordinator.last_update_success_time = None

    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(lambda h, e: h.config_entries.async_reload(e.entry_id)))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
