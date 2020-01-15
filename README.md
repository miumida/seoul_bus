# Seoul Bus Sensor(서울버스)
Seoul Bus Sensor for Home Assistant<br>

<br><br>
## Installation
- HA 설치 경로 아래 custom_components 에 파일을 넣어줍니다.<br>
  `<config directory>/custom_components/seoul_bus/__init__.py`<br>
  `<config directory>/custom_components/seoul_bus/manifest.json`<br>
  `<config directory>/custom_components/seoul_bus/sensor.py`<br>
- configuration.yaml 파일에 설정을 추가합니다.<br>
- Home-Assistant 를 재시작합니다<br>
<br><br>
## Usage
### configuration
- HA 설정에 Seoul Bus sensor를 추가합니다.<br>
```yaml
sensor:
  - platform: seoul_bus
    api_key: 'input your api key'
    api_issued_date: 'input your api issued date'
    view_type: 'M'
    stations:
      - station_id: '03198'
        name: '서울역'
        update_time:
          - start_time: '07:40'
            end_time: '08:30'
      - station_id: '24131'
        name: '잠실중학교'
        update_time:
          - start_time: '21:40'
            end_time: '22:00'
        include_buses:
          - bus_id: '100100237'
        exclude_buses:
          - bus_id: '100100237'
```
<br><br>
