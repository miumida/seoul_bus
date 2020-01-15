# Seoul Bus Sensor(서울버스)
Seoul Bus Sensor for Home Assistant 입니다.<br>
- 서울버스 도착정보를 알려줍니다.
- 정류장, 버스, 그리고 API. 모두 세가지 센서로 구성됩니다. API 센서는 옵션입니다.

<br><br>
## Version history
| Version | Date        |               |
| :-----: | :---------: | ------------- |
| v1.0    | 2020.01.15  | First version  |

<br>

## Installation
- HA 설치 경로 아래 custom_components 에 파일을 넣어줍니다.<br>
  `<config directory>/custom_components/seoul_bus/__init__.py`<br>
  `<config directory>/custom_components/seoul_bus/manifest.json`<br>
  `<config directory>/custom_components/seoul_bus/sensor.py`<br>
- configuration.yaml 파일에 설정을 추가합니다.<br>
- Home-Assistant 를 재시작합니다<br>

<br>

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
### 기본 설정값

|옵션|값|
|--|--|
|platform| (필수) seoul_bus |
|api_key| (필수) 서울버스 API KEY |
|api_issued_date| (옵션) API 발급일자. |
|view_type | (옵션) 버스센서 상태에 출력타입 |
|stations| (필수) 센서로 등록할 버스정류장 목록 |

<br>

### station별 설정값

|옵션|값|
|--|--|
|station_id| (필수) 정류장 고유번호 |
|name| (옵션) 정류장 이름 |
|update_time| (옵션) 특정구간(시작-종료)에서만 센서 업데이트가 필요한 경우, 설정 |
|include_buses| (옵션) 특정 버스만 보고 싶을 경우, 설정 |
|exclude_buses| (옵션) 특정 버스만 빼고 보고 싶을 경우, 설정 |

<br>

### 정류장 고유번호(station_id) 값 확인
- station_id는 정류장 고유번호입니다.

<br>

### view_type 설정값

|옵션|값|
|--|--|
|S| (디폴트) 버스 센서 state를 초로 표시 |
|M| 버스 센서 state를 00분00초 표시 |
|A| 버스 센서 state를 API msg로 표시 ( 00분00초후[0번째전] )|

<br>

### update_time 설정값

|옵션|값|
|--|--|
|start_time| (필수) 특정구간의 버스정보를 갱신하기 위한 시작시간 |
|end_time| (필수) 특정구간의 버스정보를 갱신하기 위한 종료시간 |

- 'HH:MM'와 같은 포맷으로 입력 필요.(24시간 체계)
- start_time은 end_time보다 이전 시간이여야 함.
- update_time을 설정하지 않는 경우, 4:00 ~ 23:59 구간에 버스정보를 갱신
