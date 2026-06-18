# 의류 관리 및 이미지 분석 API 가이드

이 API는 사용자의 옷 정보를 등록, 조회, 삭제하고, 특히 AI Vision을 통해 업로드된 사진에서 옷의 속성(카테고리, 색상, 소재 등)을 자동으로 추출하는 기능을 제공합니다.

## 1. 환경 변수

이미지 분석 기능을 사용하려면 백엔드 `.env` 파일에 아래 키가 필요합니다.

```env
GROQ_API_KEY=gsk_your_groq_api_key
```

- `GROQ_API_KEY`: Groq의 Llama-3.2 Vision 모델을 사용하여 이미지를 분석하는 데 사용됩니다.

## 2. 의류 자동 분석 및 업로드 (핵심 기능)

사용자가 옷 사진을 올리면 AI가 정보를 자동으로 추출합니다.

```http
POST /clothing/upload-and-analyze
```

- **Body**: `file` (form-data, 이미지 파일)
- **동작**:
    1. 이미지 파일을 서버에 저장 (UUID를 사용해 중복 방지)
    2. Vision AI가 사진 속 옷의 카테고리, 색상, 소재, 두께, 스타일 태그, 설명을 추출
    3. 분석 결과와 이미지 경로를 반환

### 프론트엔드 호출 예시 (JavaScript)

```js
const formData = new FormData();
formData.append('file', imageFile);

const res = await fetch('http://127.0.0.1:8000/clothing/upload-and-analyze', {
  method: 'POST',
  body: formData
});

const data = await res.json();
if (data.status === 'success') {
  console.log('AI 분석 결과:', data.analysis);
  console.log('이미지 경로:', data.image_path);
}
```

### 응답 예시 (JSON)

```json
{
  "status": "success",
  "analysis": {
    "category": "상의",
    "color": "네이비",
    "thickness": "보통",
    "material": "면",
    "tags": ["캐주얼", "심플"],
    "description": "깔끔한 네이비 컬러의 면 소재 긴팔 티셔츠입니다."
  },
  "image_path": "backend/static/uploads/a1b2c3d4-e5f6...jpg",
  "message": "이미지 분석이 완료되었습니다. 추출된 정보를 확인해주세요."
}
```

---

## 3. 의류 데이터 최종 저장

AI가 분석한 내용을 사용자가 확인(또는 수정)한 후, 최종적으로 옷장에 등록할 때 사용합니다.

```http
POST /clothing/manual-input
```

- **Body**: `WardrobeInput` 모델 (JSON)

### 요청 예시

```json
{
  "items": [
    {
      "category": "상의",
      "color": "네이비",
      "thickness": "보통",
      "material": "면",
      "tags": ["캐주얼", "심플"],
      "description": "깔끔한 네이비 컬러의 면 소재 긴팔 티셔츠입니다.",
      "image_path": "backend/static/uploads/a1b2c3d4-e5f6...jpg"
    }
  ],
  "source": "image"
}
```

---

## 4. 의류 목록 조회 및 삭제

### 모든 의류 목록 조회

```http
GET /clothing/
```

### 특정 의류 삭제

정보뿐만 아니라 서버에 저장된 **실제 이미지 파일도 함께 삭제**됩니다.

```http
DELETE /clothing/{item_id}
```

---

## 5. 데이터 모델 (ClothingItem)

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | string | 고유 ID (자동 생성) |
| `category` | string | 상의, 하의, 아우터, 신발, 기타 |
| `color` | string | 옷의 색상 |
| `thickness` | string | 얇음, 보통, 두꺼움 |
| `material` | string | 면, 울, 데님, 패딩, 나일론 등 |
| `tags` | list | 스타일 태그 (예: ["캐주얼", "오버핏"]) |
| `description`| string | AI가 생성한 옷에 대한 설명 |
| `image_path` | string | 서버에 저장된 이미지의 상대 경로 |

---

## 6. 오류 처리 및 주의사항

1. **이미지 파일 보안**: 모든 이미지는 고유한 UUID 파일명으로 저장되어 덮어쓰기 위험이 없습니다.
2. **분석 실패**: Vision API 호출 중 오류가 발생하면 기본값(`기타`, `알수없음`)을 반환하므로 서비스가 중단되지 않습니다.
3. **리소스 관리**: `DELETE` 요청 시 서버의 정적 파일도 함께 지워지므로 저장 공간을 효율적으로 관리할 수 있습니다.
4. **API 키**: `.env`에 `GROQ_API_KEY`가 없으면 분석 기능이 동작하지 않으니 반드시 확인이 필요합니다.
