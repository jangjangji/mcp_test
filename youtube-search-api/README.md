# YouTube Search API

Rust + Actix Web으로 구현된 유튜브 자막 검색 API 서버와 웹 인터페이스입니다.

## 기능

### 백엔드 API
- OpenAI 임베딩을 사용한 유사도 검색
- YouTube 동영상 검색
- 채널 정보 및 최근 영상 조회
- YouTube 자막 추출
- 채널 자막 임베딩 저장
- Supabase에서 자막 청크 검색
- RESTful API 엔드포인트
- 헬스체크 및 로깅
- CORS 지원

### 프론트엔드 웹 인터페이스
- 모던하고 반응형 웹 UI
- 5가지 주요 기능 탭
- 실시간 검색 결과 표시
- YouTube 영상 카드 레이아웃
- 로딩 상태 및 에러 처리
- Bootstrap 5 + Font Awesome

## 설치 및 실행

### 1. Rust 설치
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### 2. 프로젝트 빌드
```bash
cd youtube-search-api
cargo build
```

### 3. 환경변수 설정
```bash
cp env.example .env
# .env 파일을 편집하여 실제 API 키 입력
```

필요한 환경변수:
- `OPENAI_API_KEY`: OpenAI API 키
- `SUPABASE_URL`: Supabase 프로젝트 URL
- `SUPABASE_KEY`: Supabase API 키
- `YOUTUBE_API_KEY`: YouTube Data API v3 키

### 4. 서버 실행
```bash
cargo run
```

### 5. 웹 인터페이스 접속
브라우저에서 `http://localhost:8080` 접속

## 웹 인터페이스 기능

### 1. 유사도 검색
- 검색어와 유사한 YouTube 자막 찾기
- 유사도 점수 및 자막 청크 표시

### 2. YouTube 검색
- YouTube에서 동영상 검색
- 썸네일, 제목, 채널명, 조회수 표시

### 3. 채널 정보
- YouTube 영상 URL로 채널 정보 조회
- 최근 5개 영상 목록 표시

### 4. 자막 가져오기
- YouTube 영상의 자막 추출
- 자막 내용 표시

### 5. 채널 저장
- 채널의 모든 영상 자막을 임베딩하여 저장
- 100개 자막 청크까지 저장

## API 엔드포인트

### 웹 인터페이스
```bash
GET http://localhost:8080/          # 메인 웹 페이지
GET http://localhost:8080/static/   # 정적 파일
```

### API 엔드포인트
```bash
GET  http://localhost:8080/health                    # 헬스체크
POST http://localhost:8080/api/search               # 유사도 검색
POST http://localhost:8080/api/youtube/search       # YouTube 검색
POST http://localhost:8080/api/channel/info         # 채널 정보
POST http://localhost:8080/api/channel/save         # 채널 저장
POST http://localhost:8080/api/transcript           # 자막 가져오기
```

## API 사용 예시

### 유사도 검색
```bash
curl -X POST http://localhost:8080/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "짜파게티"}'
```

### YouTube 검색
```bash
curl -X POST http://localhost:8080/api/youtube/search \
  -H "Content-Type: application/json" \
  -d '{"query": "요리"}'
```

### 채널 정보
```bash
curl -X POST http://localhost:8080/api/channel/info \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

## 응답 예시

### 유사도 검색 결과
```json
{
  "video_id": "영상ID",
  "url": "https://www.youtube.com/watch?v=영상ID",
  "chunk_index": 2,
  "chunk_text": "짜파게티 만드는 꿀팁은...",
  "score": 0.87,
  "error": null
}
```

### YouTube 검색 결과
```json
[
  {
    "title": "영상 제목",
    "published_date": "2024-01-01T00:00:00Z",
    "channel_name": "채널명",
    "channel_id": "채널ID",
    "thumbnail_url": "썸네일URL",
    "view_count": 1000000,
    "like_count": 50000,
    "url": "https://www.youtube.com/watch?v=영상ID"
  }
]
```

## 개발

### 의존성 추가
```bash
cargo add [패키지명]
```

### 테스트
```bash
cargo test
```

### 린트
```bash
cargo clippy
```

### 프로덕션 빌드
```bash
cargo build --release
```

## 파일 구조

```
youtube-search-api/
├── Cargo.toml              # 프로젝트 설정
├── src/
│   └── main.rs             # 메인 서버 코드
├── static/
│   ├── index.html          # 메인 웹 페이지
│   └── app.js              # 프론트엔드 JavaScript
├── .gitignore              # Git 무시 파일
├── env.example             # 환경변수 예시
└── README.md               # 프로젝트 문서
```

## 기술 스택

### 백엔드
- **Rust**: 시스템 프로그래밍 언어
- **Actix Web**: 고성능 웹 프레임워크
- **Tokio**: 비동기 런타임
- **Serde**: 직렬화/역직렬화
- **Reqwest**: HTTP 클라이언트

### 프론트엔드
- **HTML5**: 마크업
- **CSS3**: 스타일링
- **JavaScript (ES6+)**: 클라이언트 사이드 로직
- **Bootstrap 5**: UI 프레임워크
- **Font Awesome**: 아이콘

### 외부 API
- **OpenAI API**: 텍스트 임베딩
- **YouTube Data API v3**: YouTube 데이터
- **Supabase**: 벡터 데이터베이스 