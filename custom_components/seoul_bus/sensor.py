import logging
import requests
import math
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from datetime import timedelta
from datetime import datetime

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_API_KEY, CONF_ICON)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

REQUIREMENTS = ['xmltodict==0.12.0']

_LOGGER = logging.getLogger(__name__)

# configuration value
CONF_API_ISSUED_DATE = 'api_issued_date'

CONF_STATIONS   = 'stations'
CONF_STATION_ID = 'station_id'
CONF_STATION_INCLUDE_BUSES = 'include_buses'
CONF_STATION_EXCLUDE_BUSES = 'exclude_buses'
CONF_STATION_UPDATE_TIME = 'update_time'
CONF_START_TIME = 'start_time'
CONF_END_TIME   = 'end_time'
CONF_BUS_ID = 'bus_id'
CONF_VIEW_TYPE = 'view_type'

# seoul bus api url
SEOUL_BUS_API_URL = 'http://ws.bus.go.kr/api/rest/stationinfo/getStationByUid?ServiceKey={}&arsId={}'

# bus properties dict
_BUS_PROPERTIES = {
    'busRouteId': '노선ID',
    'rtNm': '버스번호',
    'sectNm': '구간',
    'adirection': '방향',

    'stNm': '정류장',
    'arsId': '정류장고유번호',
    'stId': '정류장ID',
    'staOrd': '정류장순번',

    'vehId1': '가까운 버스1 ID',
    'traTime1': '가까운버스1 도착예정시간',
    'arrmsg1': '가까운버스1 메세지',

    'vehId2': '가까운 버스2 ID',
    'traTime2': '가까운버스2 도착예정시간',
    'arrmsg2': '가까운버스2 메세지',
    'syncDate': 'Sync Date',
    'start_time': '시작시간',
    'end_time': '종료시간',
    'isUpdate': 'is Update'
}

# default value
DEFAULT_NAME = 'Seoul Bus'
DEFAULT_STATION_NAME = 'Station'
DEFAULT_VIEW_TYPE = 'S'

# default icon
ICON_STATION      = 'mdi:nature-people'
ICON_BUS          = 'mdi:bus'
ICON_BUS_READY    = 'mdi:bus-clock'
ICON_BUS_ALERT    = 'mdi:bus-alert'

ICON_SIGN_CAUTION = 'mdi:sign-caution'
ICON_EYE_OFF      = 'mdi:eye-off'

# default_time
DEFAULT_START_HOUR = 3
DEFAULT_END_HOUR   = 24

# update time
MIN_TIME_BETWEEN_API_UPDATES    = timedelta(seconds=120) #

MIN_TIME_BETWEEN_API_SENSOR_UPDATES = timedelta(seconds=3600)

MIN_TIME_BETWEEN_STATION_SENSOR_UPDATES = timedelta(seconds=90) #
MIN_TIME_BETWEEN_BUS_SENSOR_UPDATES = timedelta(seconds=10)

# attribute value
ATTR_ROUTE_ID = 'busRouteId'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
    vol.Optional(CONF_API_ISSUED_DATE): cv.string,
    vol.Required(CONF_STATIONS): vol.All(cv.ensure_list, [{
        vol.Required(CONF_STATION_ID): cv.string,
        vol.Optional(CONF_NAME, default = DEFAULT_STATION_NAME): cv.string,
        vol.Optional(CONF_STATION_UPDATE_TIME, default=[]): vol.All(cv.ensure_list, [{
            vol.Required(CONF_START_TIME, default = ''): cv.string,
            vol.Required(CONF_END_TIME, default =''): cv.string,
        }]),
        vol.Optional(CONF_STATION_INCLUDE_BUSES, default=[]): vol.All(cv.ensure_list, [{
            vol.Required(CONF_BUS_ID, default = ''): cv.string,
        }]),
        vol.Optional(CONF_STATION_EXCLUDE_BUSES, default=[]): vol.All(cv.ensure_list, [{
            vol.Required(CONF_BUS_ID, default = ''): cv.string,
        }]),
    }]),
    vol.Optional(CONF_VIEW_TYPE, default = DEFAULT_VIEW_TYPE): cv.string,
})

# 현재시간이 두시간 사이구간에 존재하는지 체크
def isBetweenNowTime(start, end):
    rtn = False

    now  = datetime.now()
    year = now.year
    mon  = now.month
    day  = now.day
    hour = now.hour
    min  = now.minute

    nowTime = datetime(year, mon, day, hour, min)

    try:
        arrTm1 = start.split(":")
        arrTm2 = end.split(":")

        st  = datetime(year, mon, day, int(arrTm1[0]), int(arrTm1[1]))
        ed  = datetime(year, mon, day, int(arrTm2[0]), int(arrTm2[1]))

        if nowTime >= st and nowTime <= ed:
            rtn = True
        else:
            rtn = False
    except Excption as ex:
        _LOGGER.error('Failed to isBetweenNowTime() Seoul Bus Method Error: %s', ex)

    return rtn

# 초를 분으로 변환
def second2min(val):
    try:
        if 60 >  int(val):
            return '{}초'.format(val)
        else:
            min = math.floor(int(val)/60)
            sec = int(val)%60
            return '{}분{}초'.format(str(min), str(sec))
    except Exception as ex:
        _LOGGER.error('Failed to second2min() Seoul Bus Method Error: %s', ex)

    return val

#xml2dict 문제 처리를 위함
def cover_list(dict):
    if not dict:
        return []
    elif isinstance(dict, list):
        return dict
    else:
        return [dict]


def setup_platform(hass, config, add_entities, discovery_info=None):
    name = config.get(CONF_NAME)
    api_key         = config.get(CONF_API_KEY)
    api_issued_date = config.get(CONF_API_ISSUED_DATE)
    stations        = config.get(CONF_STATIONS)
    view_type       = config.get(CONF_VIEW_TYPE)

    sensors = []

    # api sensor add
    if api_issued_date is not None:
        sensors += [apiSensor(api_issued_date)]

    # sensor add
    for station in stations:
        api = SeoulBusAPI(api_key, station[CONF_STATION_ID], station[CONF_STATION_UPDATE_TIME], view_type)

        # station sensor add
        sensor = BusStationSensor(station[CONF_STATION_ID], station[CONF_NAME], station[CONF_STATION_INCLUDE_BUSES], station[CONF_STATION_EXCLUDE_BUSES], station[CONF_STATION_UPDATE_TIME], api)
        sensor.update()
        sensors += [sensor]

        # bus sensor add
        for bus_id, value in sensor.buses.items():
            try:
                sensors += [BusSensor(station[CONF_STATION_ID], station[CONF_NAME], station[CONF_STATION_UPDATE_TIME], bus_id, value.get(CONF_NAME, ''), value, api)]
            except Exception as ex:
                _LOGGER.error('[Seoul Bus] Failed to BusSensor add  Error: %s', ex)

    add_entities(sensors, True)

#api key 만료일 센서
class apiSensor(Entity):
    def __init__(self, api_issued_date):
        self._issued_date = api_issued_date
        self._dday = None

    @property
    def entity_id(self):
        """Return the entity ID."""
        return 'sensor.seoul_bus_api_info'

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        return '서울버스 API정보'

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi:key-variant'

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._dday

    @Throttle(MIN_TIME_BETWEEN_API_SENSOR_UPDATES)
    def update(self):
        """Get the latest state of the sensor."""
        tmp = self._issued_date.split("-")

        expired = datetime( year=int(tmp[0])+2, month=int(tmp[1]), day=int(tmp[2]) )

        exp2day = expired - datetime.today()

        self._dday = exp2day.days

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return '일 후 만료'

    @property
    def device_state_attributes(self):
        """Attributes."""
        data = { 'API발급일' : self._issued_date,
                 '만료까지' : self._dday  }
        return data

#서울버스 api
class SeoulBusAPI:
    """Seoul Bus API."""
    def __init__(self, api_key, station_id, update_time, view_type):
        """Initialize the Seoul Bus API."""
        self._api_key = api_key
        self._station_id  = station_id
        self._update_time = update_time
        self._isUpdate  = True

        self._isError   = False
        self._errorCd   = None
        self._errorMsg  = None

        self._view_type = view_type
        self._sync_date = None
        self.result = {}

    def update(self):
        """Update function for updating api information."""
        dt = datetime.now()
        syncDate = dt.strftime("%Y-%m-%d %H:%M:%S")

        self._sync_date = syncDate

        if dt.hour > DEFAULT_START_HOUR and dt.hour < DEFAULT_END_HOUR:
            self._isUpdate = True
        else:
            self._isUpdate = False

        if len(self._update_time) > 0:
            for item in self._update_time:
                stt_tm = item['start_time']
                end_tm = item['end_time']

            self._isUpdate = isBetweenNowTime(stt_tm, end_tm)

        import xmltodict
        try:
            url = SEOUL_BUS_API_URL.format(self._api_key, self._station_id)

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            page = response.content.decode('utf8')

            hdr = xmltodict.parse(page)['ServiceResult']['msgHeader']

            bus_dict = {}

            if ( hdr['headerCd'] != '0'):
                self._isError = True

                self._errorCd = hdr['headerCd']
                self._errorMsg = hdr['headerMsg']

                _LOGGER.error('Failed to update Seoul Bus API status Error: %s', hdr['headerMsg'] )
            else:
                self._isError = False
                self._errorCd = None
                self._errorMsg = None

                rows = xmltodict.parse(page)['ServiceResult']['msgBody']['itemList']

                for row in cover_list(rows):
                    bus_dict[row[ATTR_ROUTE_ID]] = {
                        'rtNm': row['rtNm'],
                        'busRouteId': row['busRouteId'],
                        'adirection': row['adirection'],
                        'sectNm': row['sectNm'],

                        'stNm':   row['stNm'],
                        'arsId':  row['arsId'],
                        'stId':   row['stId'],
                        'staOrd': row['staOrd'],

                        'vehId1':   row['vehId1'],
                        'traTime1': row['traTime1'],
                        'arrmsg1':  row['arrmsg1'],

                        'vehId2':   row['vehId2'],
                        'traTime2': row['traTime2'],
                        'arrmsg2':  row['arrmsg2'],
                        'syncDate': syncDate,
                        'isUpdate': self._isUpdate
                    }

            self.result = bus_dict
            #_LOGGER.debug('Seoul Bus API Request Result: %s', self.result)
        except Exception as ex:
            _LOGGER.error('Failed to update Seoul Bus API status Error: %s', ex)
            raise

# station sensor
class BusStationSensor(Entity):
    def __init__(self, id, name, include_buses, exclude_buses, update_time, api):
        self._station_id = id
        self._station_name = name
        self._include_buses = include_buses
        self._exclude_buses = exclude_buses
        self._update_time   = update_time
        self._isUpdate = None
        self._stt_time = None
        self._end_time = None

        self._sync_date = None

        self._api   = api
        self._icon  = ICON_STATION
        self._state = None
        self.buses  = {}

    @property
    def entity_id(self):
        """Return the entity ID."""
        return 'sensor.seoul_bus_s{}'.format(self._station_id)

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if not self._station_name:
            return 'St.{}'.format(self._station_id)
        return '{}({})'.format(self._station_name, self._station_id)

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        if self._api._isError:
            return ICON_SIGN_CAUTION

        if not self._isUpdate:
            return ICON_EYE_OFF

        if not self._api._isUpdate:
            return ICON_EYE_OFF

        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._api._isError:
            return 'Error'

        if not self._isUpdate:
            return '-'

        if not self._isUpdate:
            return '-'

        count = 0
        for value in self.buses.values():
            if value.get('vehId1', '0') != '0':
                count += 1
        return '운행종료' if count == 0 else '운행중'

    @Throttle(MIN_TIME_BETWEEN_STATION_SENSOR_UPDATES)
    def update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        if self._isUpdate is None:
            self._api.update()

        dt = datetime.now()
        syncDate = dt.strftime("%Y-%m-%d %H:%M:%S")

        self._sync_date = syncDate

        if len(self._update_time) > 0:
            stt_tm = None
            end_tm = None

            for item in self._update_time:
                stt_tm = item['start_time']
                end_tm = item['end_time']

                self._stt_time = stt_tm
                self._end_time = end_tm

            self._isUpdate = isBetweenNowTime(stt_tm, end_tm)

        if self._isUpdate:
            self._api.update()

        buses_dict = self._api.result

        for item in self._exclude_buses:
            buses_dict.pop(item['bus_id'], {})

        if not self._include_buses:
            self.buses = buses_dict
        else:
            for item in self._include_buses:
                bus = buses_dict.get(item['bus_id'], {})
                self.buses[item['bus_id']] = bus

    @property
    def device_state_attributes(self):
        """Attributes."""
        attr = {}

        # API Error Contents Attributes Add
        if self._api._isError :
            attr['API Error Code'] = self._api._errorCd
            attr['API Error Msg'] = self._api._errorMsg

        for key in sorted(self.buses):
            attr['{} [{}]'.format(self.buses[key].get('rtNm', key), self.buses[key].get('adirection', '-'))] = (self.buses[key].get('arrmsg1','-') if self.buses[key].get('vehId1','0')=='0' else '{} {}'.format(self.buses[key].get('traTime1', '0'), '초') ) 

        attr['Sync Date'] = self._sync_date
        attr['is Update'] = self._isUpdate
        attr['start time'] = self._stt_time
        attr['end time']   = self._end_time

        return attr

# bus sensor
class BusSensor(Entity):
    def __init__(self, station_id, station_name, station_update_time, bus_id, bus_name, values,  api):
        self._station_id   = station_id
        self._station_name = station_name
        self._station_update_time = station_update_time
        self._bus_id   = bus_id
        self._bus_name = bus_name

        self._isUpdate = None
        self._stt_time = None
        self._end_time = None

        self._api = api
        self._view_type = api._view_type
        self._state = None
        self._data  = {}

        self._rtNm = values['rtNm']
        self._adirection = values['adirection']
        self._sectNm = values['sectNm']

        self._vehId1   = values['vehId1']
        self._traTime1 = values['traTime1']
        self._arrmsg1  = values['arrmsg1']

        self._vehId2   = values['vehId2']
        self._traTime2 = values['traTime2']
        self._arrmsg2  = values['arrmsg2']

    @property
    def entity_id(self):
        """Return the entity ID."""
        return 'sensor.seoul_bus_{}_{}'.format(self._station_id, self._bus_id)

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        station_name = self._station_name

        if not self._station_name:
            station_name = 'St.{}'.format(self._station_id)

        if not self._bus_name:
            return '{} {} [{}]'.format(station_name, self._rtNm, self._adirection )

        return self._bus_name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        if not self._isUpdate:
            return ICON_BUS_READY

        return ICON_BUS_ALERT if (self._data['vehId1'] == '0' and self._data['vehId2'] == '0') else ICON_BUS

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        if not self._isUpdate:
            return ''

        if self._view_type == 'S':
            return '초'
        else:
            return ''

    @property
    def state(self):
        """Return the state of the sensor."""
        if not self._isUpdate:
            return '-'

        if self._view_type == 'S':
            return self._data['traTime1']

        if self._view_type == 'M':
            return '0' if self._data['traTime1'] == '0' else second2min(self._data['traTime1'])

        if self._view_type == 'A':
            return self._data['arrmsg1']

        return '-'

    @Throttle(MIN_TIME_BETWEEN_BUS_SENSOR_UPDATES)
    def update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        dt = datetime.now()
        syncDate = dt.strftime("%Y-%m-%d %H:%M:%S")

        self._sync_date = syncDate


        if len(self._station_update_time) > 0:
            stt_tm = None
            end_tm = None

            for item in self._station_update_time:
                stt_tm = item['start_time']
                end_tm = item['end_time']

                self._stt_time = stt_tm
                self._end_time = end_tm

            self._isUpdate = isBetweenNowTime(stt_tm, end_tm)

        buses_dict = self._api.result
        self._data = buses_dict.get(self._bus_id,{})

        if not self._isUpdate:
            self._data['vehId1']   = '0'
            self._data['vehId2']   = '0'
            self._data['traTime1'] = '0'
            self._data['traTime2'] = '0'
            self._data['arrmsg1']  = '-'
            self._data['arrmsg2']  = '-'


    @property
    def device_state_attributes(self):
        """Attributes."""
        attr = {}

        for key in self._data:
           attr[_BUS_PROPERTIES[key]] = self._data[key]

        attr[_BUS_PROPERTIES['syncDate']] = self._sync_date

        attr[_BUS_PROPERTIES['isUpdate']]   = self._isUpdate
        attr[_BUS_PROPERTIES['start_time']] = self._stt_time
        attr[_BUS_PROPERTIES['end_time']]   = self._end_time

        return attr
