# 날씨 API 사용 가이드

날씨 API는 사용자가 입력한 장소, 주소, 동 이름, 도시명, 위도/경도, 또는 기상청 격자 좌표를 받아 현재 날씨 정보를 반환합니다.

프론트 팀은 API 키를 직접 사용하지 않습니다. 프론트는 백엔드의 `/weather` API만 호출하면 됩니다.

## 1. 환경 변수

백엔드 `.env` 파일에 아래 키가 필요합니다.

```env
KMA_API_KEY=기상청_APIHub_authKey
KAKAO_REST_API_KEY=카카오_REST_API_KEY
```

- `KMA_API_KEY`: 기상청 APIHub의 동네예보 API 호출에 사용합니다.
- `KAKAO_REST_API_KEY`: 주소, 동 이름, 장소명을 위도/경도로 바꾸는 데 사용합니다.

## 2. 현재 날씨 조회

### 장소명/주소/동 이름으로 조회

프론트에서는 보통 이 API를 쓰면 됩니다.

```http
GET /weather/current?place={사용자입력값}
```

예시:

```http
GET /weather/current?place=홍대입구역
GET /weather/current?place=역삼동
GET /weather/current?place=서울 강남구 역삼동
GET /weather/current?place=부산 해운대구 우동
```

프론트 예시:

```js
const place = "홍대입구역";
const res = await fetch(
  `http://127.0.0.1:8000/weather/current?place=${encodeURIComponent(place)}`
);
const weather = await res.json();
```

### 도시명으로 조회

일부 주요 도시는 직접 조회할 수 있습니다.

```http
GET /weather/current?city=서울
GET /weather/current?city=부산
GET /weather/current?city=제주
```

### 기상청 격자 좌표로 조회

카카오 API 없이 기상청 API만 테스트할 때 유용합니다.

```http
GET /weather/current?nx=60&ny=127
```

`nx=60`, `ny=127`은 서울 기준 격자입니다.

### 위도/경도로 조회

이미 위치 좌표를 알고 있다면 직접 넣을 수 있습니다.

```http
GET /weather/current?latitude=37.55687&longitude=126.92378
```

## 3. 위치 검색

장소 후보만 먼저 보고 싶을 때 사용합니다.

```http
GET /weather/search?query={검색어}
```

예시:

```http
GET /weather/search?query=역삼동
GET /weather/search?query=홍대입구역
```

응답에는 장소명, 위도, 경도, 기상청 격자 `nx`, `ny`가 포함됩니다.

## 4. 응답 예시

```json
{
  "location": {
    "name": "홍대입구역 2호선",
    "country": "Korea",
    "country_code": "KR",
    "admin1": null,
    "latitude": 37.5568707448873,
    "longitude": 126.923778562273,
    "nx": 59,
    "ny": 126,
    "timezone": "Asia/Seoul"
  },
  "time": "20260608T2300",
  "temperature": 21.1,
  "apparent_temperature": 21.1,
  "relative_humidity": 63,
  "precipitation": 0.0,
  "rain": 0.0,
  "snowfall": 0.0,
  "weather_code": 1,
  "weather_description": "Clear",
  "cloud_cover": 0,
  "wind_speed": 2.0,
  "wind_direction": 284,
  "wind_gusts": null,
  "is_day": null,
  "daily_min_temperature": null,
  "daily_max_temperature": null,
  "daily_precipitation_probability": null,
  "clothing_hints": [
    "Mild: long sleeves or a light cardigan should be enough."
  ],
  "source": "KMA APIHub"
}
```

## 5. 프론트 팀에서 사용할 값

프론트 화면에는 아래 값을 우선 표시하면 됩니다.

| 필드 | 의미 | 화면 표시 예시 |
| --- | --- | --- |
| `location.name` | 조회된 장소명 | 홍대입구역 2호선 |
| `temperature` | 현재 기온 | 21.1도 |
| `apparent_temperature` | 체감온도 | 체감 21.1도 |
| `relative_humidity` | 습도 | 습도 63% |
| `weather_description` | 날씨 상태 | Clear |
| `precipitation` | 강수량 | 강수량 0mm |
| `rain` | 비 | 비 없음 |
| `snowfall` | 눈 | 눈 없음 |
| `wind_speed` | 풍속 | 2.0m/s |
| `wind_direction` | 풍향 | 284도 |
| `clothing_hints` | 날씨 기반 옷차림 힌트 | 긴팔 또는 얇은 가디건 추천 |

프론트 표시 문구 예시:

```text
홍대입구역 2호선 현재 날씨
기온 21.1도 / 습도 63% / Clear
강수 없음, 풍속 2.0m/s
추천: 긴팔 또는 얇은 가디건
```

## 6. 추천 로직 팀에서 사용할 값

추천 로직은 아래 필드를 우선 사용하면 됩니다.

### 필수 입력값

| 필드 | 추천 로직 활용 |
| --- | --- |
| `temperature` | 옷 두께, 반팔/긴팔/아우터 판단 |
| `apparent_temperature` | 실제 체감 기준 보정 |
| `relative_humidity` | 습하고 더운 날 얇은 소재 추천 |
| `precipitation` | 비/눈 대비 여부 판단 |
| `rain` | 우산, 방수 신발, 젖어도 되는 소재 추천 |
| `snowfall` | 방한, 미끄럼 방지 신발 추천 |
| `weather_description` | 맑음/흐림/비/눈 상태 설명 |
| `wind_speed` | 바람막이, 겉옷 필요 여부 판단 |
| `clothing_hints` | 기본 날씨 기반 추천 문장 |

### 추천 로직 예시 기준

```text
temperature < 8
→ 코트, 패딩, 두꺼운 니트 추천

8 <= temperature < 16
→ 자켓, 가디건, 맨투맨 추천

16 <= temperature < 23
→ 긴팔, 얇은 가디건 추천

23 <= temperature < 28
→ 반팔, 얇은 셔츠, 통풍되는 하의 추천

temperature >= 28
→ 얇고 밝은 옷, 통풍 좋은 소재 추천

precipitation > 0 or rain > 0
→ 우산, 방수 아우터, 젖어도 되는 신발 추천

wind_speed >= 8
→ 바람막이 또는 겉옷 추천
```

## 7. 오류 처리

프론트에서는 `response.ok`가 false일 때 `detail` 값을 표시하거나 기본 오류 문구를 보여주면 됩니다.

```js
const res = await fetch(`/weather/current?place=${encodeURIComponent(place)}`);
const data = await res.json();

if (!res.ok) {
  throw new Error(data.detail || "날씨 정보를 가져오지 못했습니다.");
}
```

주요 오류:

| 오류 | 의미 | 해결 |
| --- | --- | --- |
| `KMA_API_KEY is not set` | 기상청 키 없음 | 백엔드 `.env` 확인 |
| `KMA APIHub authorization failed` | 기상청 APIHub 인증 실패 | authKey 또는 API 신청 상태 확인 |
| `KAKAO_REST_API_KEY is required` | `place` 검색에 필요한 카카오 키 없음 | 백엔드 `.env` 확인 |
| `Kakao Local API request failed` | 카카오 API 호출 실패 | REST API 키, 로컬 API 활성화 확인 |
| `Cannot find place/address` | 장소 검색 실패 | 더 구체적인 주소나 장소명 입력 |

## 8. 백엔드 담당 참고

현재 날씨 API는 아래 순서로 동작합니다.

```text
place 입력
→ Kakao Local API로 주소/장소 검색
→ 위도/경도 추출
→ 기상청 nx/ny 격자 변환
→ KMA APIHub 동네예보 API 호출
→ 프론트/추천 로직용 JSON 반환
```

프론트와 추천 팀은 기상청/카카오 키를 직접 다루지 않습니다.
