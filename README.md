# Seoul Bus Sensor(서울버스)

![HAKC)][hakc-shield]
![HACS][hacs-shield]
![Version v1.4][version-shield]

Seoul Bus Sensor for Home Assistant 입니다.<br>
- 서울버스 도착정보를 알려줍니다.
- 지정한 정류장에 도착예정인 버스를 확인할 수 있습니다.
- 정류장, 버스, 그리고 API. 모두 세가지 센서로 구성됩니다. API 센서는 옵션입니다.

![screenshot_1](https://github.com/miumida/seoul_bus/blob/master/image/Screenshot_1.png?raw=true)<br>

![screenshot_2](https://github.com/miumida/seoul_bus/blob/master/image/Screenshot_2.png?raw=true)<br>
[ 버스 센서 ]<br>
![screenshot_4](https://github.com/miumida/seoul_bus/blob/master/image/Screenshot_4.png?raw=true)<br>
[ API 센서 ]<br>
![screenshot_5](https://github.com/miumida/seoul_bus/blob/master/image/Screenshot_5.png?raw=true)<br>

<br><br>
## Version history
| Version | Date        | 내용              |
| :-----: | :---------: | ----------------------- |
| v1.0    | 2020.01.15  | First version  |
| v1.1    | 2020.01.16  | Exception 처리 추가. API 오류코드/메세지 표시  |
| v1.2    | 2020.01.20  | xml2dict 문제점 보완. 정류장센서 update_time 구간만 상태반영  |
| v1.3    | 2020.04.21  | 정류장/버스센서 update_time 구간 상태반영 수정.  |
| v1.4    | 2020.04.21  | 버스센서 속성명 변경  |
| v1.4    | 2021.10.24  | manifest.json add version info  |

<br>

## Installation
### Manual
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

### API KEY 발급
공공데이터포털에서 정류소정보조회 서비스(<https://www.data.go.kr/data/15000314/openapi.do>)를 발급신청하여 인증키를 발급받습니다.

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
- 서울 버스도착정보 - 버스노선 사이트(<http://bus.go.kr/searchResult6.jsp>)에 접속하여 정류장을 조회하여 ```정류소번호```를 확인합니다.

![screenshot_3](https://github.com/miumida/seoul_bus/blob/master/image/Screenshot_3.png?raw=true)<br>
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

<br>

### include_buses/exclude_buses 버스id(노선id)설정값
- include_buses/exclude_buses의 버스id(노선id)를 입력하여 설정한다.
- 서울특별시 버스노선 기본정보 항목정보(<http://data.seoul.go.kr/dataList/OA-15262/F/1/datasetView.do>)에서 버스노스id를 확인하여 입력한다.

<br>

## 참고사이트
[1]서울 버스도착정보 - 버스노선 사이트(<http://bus.go.kr/searchResult6.jsp>)<br>
[2]서울특별시 버스노선 기본정보 항목정보(<http://data.seoul.go.kr/dataList/OA-15262/F/1/datasetView.do>)

[version-shield]: https://img.shields.io/badge/version-v1.4.1-orange.svg
[hakc-shield]: https://img.shields.io/badge/HAKC-Enjoy-blue.svg
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-red.svg
