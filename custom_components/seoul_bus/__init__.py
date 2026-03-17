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
        now = datetime.now().strftime("%H:%M")
        start, end = conf[CONF_START_TIME][:5], conf[CONF_END_TIME][:5]

        # 시간 범위 체크 (같으면 무조건 실행)
        if start != end and not (start <= now <= end):
            # 시간 외 구간: 기존 데이터를 유지하여 센서 사라짐 방지
            prev_data = coordinator.data if coordinator.data and isinstance(coordinator.data, dict) else {}
            return {"status": "waiting", "items": prev_data.get("items", [])}

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

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    if unload_ok: hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
