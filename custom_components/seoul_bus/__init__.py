import logging
from datetime import datetime, timedelta
import xmltodict
import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import CONF_API_KEY
from .const import DOMAIN, CONF_STATION_ID, CONF_START_TIME, CONF_END_TIME

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    async def async_update_data():
        conf = {**entry.data, **entry.options}
        
        # 현재 시간과 설정 시간 모두 HH:MM 포맷으로 통일하여 비교
        now = datetime.now().strftime("%H:%M")
        start = conf.get(CONF_START_TIME, "00:00")[:5]
        end = conf.get(CONF_END_TIME, "00:00")[:5]

        is_waiting = False
        if start != end:
            if not (start <= now <= end):
                is_waiting = True

        if is_waiting:
            # 대기 시간 중 기존 데이터 유지
            old_items = coordinator.data.get("items", []) if coordinator.data and isinstance(coordinator.data, dict) else []
            return {"status": "waiting", "items": old_items}

        url = f"http://ws.bus.go.kr/api/rest/stationinfo/getStationByUid?ServiceKey={conf[CONF_API_KEY]}&arsId={conf[CONF_STATION_ID]}"
        try:
            async with async_timeout.timeout(15):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        res_text = await response.text()
                        data = xmltodict.parse(res_text)
                        msg_body = data.get('ServiceResult', {}).get('msgBody', {})
                        items = msg_body.get('itemList', [])
                        res = items if isinstance(items, list) else ([items] if items else [])
                        return {"status": "active", "items": res}
        except Exception as err:
            raise UpdateFailed(f"API Error: {err}")

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name=f"{DOMAIN}_{entry.data[CONF_STATION_ID]}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=60),
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(lambda h, e: h.config_entries.async_reload(e.entry_id)))
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True
