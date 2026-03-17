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
    """Set up Seoul Bus from a config entry."""
    
    async def async_update_data():
        # 데이터와 옵션을 합쳐서 가져옵니다.
        conf = {**entry.data, **entry.options}
        
        # [중요 수정] 현재 시각과 설정 시각을 모두 HH:MM 포맷(5자리)으로 통일합니다.
        now = datetime.now().strftime("%H:%M")
        start = conf.get(CONF_START_TIME, "00:00")[:5]
        end = conf.get(CONF_END_TIME, "00:00")[:5]

        # 시작 시간과 종료 시간이 다를 때만 시간 제한 로직 작동
        is_waiting = False
        if start != end:
            # 시작 시각이 종료 시각보다 클 경우 (예: 23:00 ~ 05:00) 처리 포함
            if start < end:
                if not (start <= now <= end):
                    is_waiting = True
            else: # 자정을 넘기는 시간 설정 처리
                if not (now >= start or now <= end):
                    is_waiting = True

        if is_waiting:
            _LOGGER.debug("서울 버스: 현재 시간(%s)은 수집 제외 시간(%s~%s)입니다.", now, start, end)
            # 대기 시간에는 빈 목록이 아닌 기존 데이터를 유지하거나 상태만 표시
            old_data = coordinator.data if coordinator.data else {"status": "waiting", "items": []}
            return {**old_data, "status": "waiting"}

        # API 호출 부분
        url = f"http://ws.bus.go.kr/api/rest/stationinfo/getStationByUid?ServiceKey={conf[CONF_API_KEY]}&arsId={conf[CONF_STATION_ID]}"
        
        try:
            async with async_timeout.timeout(15):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        res_text = await response.text()
                        data = xmltodict.parse(res_text)
                        
                        msg_body = data.get('ServiceResult', {}).get('msgBody', {})
                        items = msg_body.get('itemList', [])
                        
                        # 아이템이 하나일 경우 리스트로 변환
                        res = items if isinstance(items, list) else ([items] if items else [])
                        return {"status": "active", "items": res}
                        
        except Exception as err:
            _LOGGER.error("서울 버스 API 호출 중 오류 발생: %s", err)
            raise UpdateFailed(f"API Error: {err}")

    # 코디네이터 설정 (1분 간격 업데이트)
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.data[CONF_STATION_ID]}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=60),
    )

    # 첫 데이터 가져오기
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # 옵션이 업데이트되면 통합구성요소를 다시 로드
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
