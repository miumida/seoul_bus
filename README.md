# 서울 버스(Seoul Bus)

![HAKC)][hakc-shield]
![HACS][hacs-shield]
![Version v2.0.0][version-shield]

Seoul Bus Sensor for Home Assistant 입니다.<br>
- 서울버스 도착정보를 알려줍니다.
- 지정한 정류장에 도착예정인 버스를 확인할 수 있습니다.
- Murianwind님이 리뉴얼 해주셨습니다. 감사합니다.

<br><br>
## Version history
| Version | Date        | 내용              |
| :-----: | :---------: | ----------------------- |
| v1.0.0  | 2020.01.15  | First version  |
| v2.0.0  | 2026.03.19  | Renewal version. (Thx. Murianwind) |

<br>

## Installation
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=miumida&repository=seoul_bus&category=Integration)
### HACS
- HACS > SETTINGS 메뉴 선택
- ADD CUSTOM REPOSITORY에 'https://github.com/miumida/seoul_bus' 입력하고 Category에 'integration' 선택 후, 저장
- HACS > INTEGRATIONS 메뉴 선택 후, 검색하여 설치
<br><br>
### Manual
- HA 설치 경로 아래 custom_components 에 파일을 넣어줍니다.<br>
  `<config directory>/custom_components/seoul_bus/전체파일`<br>
- Home-Assistant 를 재시작합니다<br>

<br>

## Usage
### Custom Integration
- 구성 > 통합구성요소 > 통합구성요소 추가하기 > 서울 버스(Seoul Bus) 선택 > 설정값 입력 후, 확인.
- HA 설정에 서울 버스(Seoul Bus)를 추가합니다.<br>
### Configuration(yaml) : Custom Integration으로 등록해주세요!
- HA설정에 서울 버스(Seoul Bus)를 추가합니다<br>
- v2.0.0 이상부터는 통합구성요소만 지원합니다.<br>
<br><br>
### 기본 설정값

|옵션|값|
|--|--|
|api_key| (필수) 서울버스 API KEY |
|station_id| (필수) 정류소ID |
|station_name | (옵션) 정류소 이름 |
|start_time| (옵션) 특정구간의 버스정보를 갱신하기 위한 시작시간 |
|end_time| (옵션) 특정구간의 버스정보를 갱신하기 위한 종료시간 |
|include_buses| (옵션) 대상 버스 목록 |

<br>

### API KEY 발급
공공데이터포털에서 [서울특별시_정류소정보조회 서비스](<https://www.data.go.kr/data/15000303/openapi.do>)를 발급신청하여 인증키를 발급받습니다.

<br>

### 정류장 고유번호(station_id) 값 확인
- station_id는 정류장 고유번호입니다.
- 서울 버스도착정보 - 버스노선 사이트(<http://bus.go.kr/searchResult6.jsp>)에 접속하여 정류장을 조회하여 ```정류소번호```를 확인합니다.

![screenshot_3](https://github.com/miumida/seoul_bus/blob/master/image/Screenshot_3.png?raw=true)<br>
<br>

### include_buses/exclude_buses 버스id(노선id)설정값
- include_buses/exclude_buses의 버스id(노선id)를 입력하여 설정한다.
- 서울특별시 버스노선 기본정보 항목정보(<http://data.seoul.go.kr/dataList/OA-15262/F/1/datasetView.do>)에서 버스노스id를 확인하여 입력한다.

<br>

## 참고사이트
[1]서울 버스도착정보 - 버스노선 사이트(<http://bus.go.kr/searchResult6.jsp>)<br>
[2]서울특별시 버스노선 기본정보 항목정보(<http://data.seoul.go.kr/dataList/OA-15262/F/1/datasetView.do>)

[version-shield]: https://img.shields.io/badge/version-v2.0.0-orange.svg
[hakc-shield]: https://img.shields.io/badge/HAKC-Enjoy-blue.svg
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-red.svg
