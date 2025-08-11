# YouTube AI Platform - 독립적인 MCP 서버 시스템

이 프로젝트는 YouTube AI Platform을 위한 독립적인 MCP(Model Context Protocol) 서버 시스템입니다.

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   YouTube MCP   │    │   Video MCP     │    │   Rust Backend  │
│   Server        │    │   Server        │    │   API Server    │
│   (포트 8001)   │    │   (포트 8002)   │    │   (포트 3000)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Supabase DB   │
                    │   (벡터 DB)     │
                    └─────────────────┘
```

## 📁 프로젝트 구조

```
youtube-ai-platform/
├── python/
│   ├── youtube_mcp_server.py          # YouTube 전용 MCP 서버
│   ├── video_mcp_server.py            # 비디오 처리 전용 MCP 서버
│   ├── youtube_mcp_http_server.py     # YouTube MCP HTTP 래퍼
│   ├── video_mcp_http_server.py       # 비디오 MCP HTTP 래퍼
│   ├── video_search_system.py         # 기존 비디오 검색 시스템
│   ├── requirements.txt               # Python 의존성
│   └── Dockerfile                     # Python 컨테이너
├── backend/
│   ├── src/main.rs                   # Rust 백엔드
│   └── Dockerfile                     # Rust 컨테이너
├── docker-compose.yml                 # 전체 시스템 오케스트레이션
├── env.example                        # 환경 변수 예시
└── README_MCP_SERVERS.md             # 이 파일
```

## 🚀 서비스 설명

### 1. YouTube MCP 서버 (포트 8001)
- **기능**: YouTube 데이터 처리 및 분석
- **도구들**:
  - `youtube_search`: YouTube 비디오 검색
  - `youtube_get_video_info`: 비디오 상세 정보
  - `youtube_get_channel_info`: 채널 정보
  - `youtube_get_comments`: 댓글 가져오기
  - `youtube_analyze_trending`: 트렌딩 분석

### 2. Video MCP 서버 (포트 8002)
- **기능**: 비디오 분석, 검색, 처리
- **도구들**:
  - `video_search`: 텍스트로 비디오 검색
  - `video_add_to_db`: 비디오 DB 추가
  - `video_get_info`: 비디오 정보 조회
  - `video_extract_frames`: 프레임 추출
  - `video_analyze_content`: 내용 분석
  - `video_clear_db`: 비디오 삭제

### 3. Rust 백엔드 (포트 3000)
- **기능**: HTTP 클라이언트로 MCP 서버들과 통신
- **역할**: 프론트엔드와 MCP 서버들 사이의 중재자

## 🛠️ 설치 및 실행

### 1. 환경 변수 설정
```bash
cp env.example .env
# .env 파일을 편집하여 실제 값들을 입력
```

### 2. Docker Compose로 실행
```bash
docker-compose up --build
```

### 3. 개별 서비스 실행
```bash
# YouTube MCP 서버만 실행
docker-compose up youtube-mcp-server

# Video MCP 서버만 실행
docker-compose up video-mcp-server

# 백엔드만 실행
docker-compose up backend
```

## 📡 API 엔드포인트

### YouTube MCP HTTP 서버 (포트 8001)
- `GET /` - 서버 상태 확인
- `GET /health` - 헬스 체크
- `POST /youtube/search` - YouTube 비디오 검색
- `POST /youtube/video/info` - 비디오 상세 정보
- `POST /youtube/channel/info` - 채널 정보
- `POST /youtube/comments` - 댓글 가져오기
- `POST /youtube/trending` - 트렌딩 분석
- `GET /tools` - 사용 가능한 도구 목록

### Video MCP HTTP 서버 (포트 8002)
- `GET /` - 서버 상태 확인
- `GET /health` - 헬스 체크
- `POST /video/search` - 비디오 검색
- `POST /video/add` - 비디오 DB 추가
- `POST /video/info` - 비디오 정보 조회
- `POST /video/extract` - 프레임 추출
- `POST /video/analyze` - 내용 분석
- `POST /video/clear` - 비디오 삭제
- `GET /tools` - 사용 가능한 도구 목록

## 🔧 개발 및 테스트

### 개별 서버 테스트
```bash
# YouTube MCP 서버 테스트
curl -X POST http://localhost:8001/youtube/search \
  -H "Content-Type: application/json" \
  -d '{"query": "강아지", "max_results": 5}'

# Video MCP 서버 테스트
curl -X POST http://localhost:8002/video/search \
  -H "Content-Type: application/json" \
  -d '{"query": "강아지가 물속에서 헤엄치는 장면"}'
```

### 로그 확인
```bash
# YouTube MCP 서버 로그
docker-compose logs youtube-mcp-server

# Video MCP 서버 로그
docker-compose logs video-mcp-server

# 백엔드 로그
docker-compose logs backend
```

## 🔄 데이터 처리 흐름

1. **YouTube 데이터 처리**:
   ```
   YouTube API → YouTube MCP 서버 → Supabase DB
   ```

2. **비디오 처리**:
   ```
   비디오 파일 → Video MCP 서버 → CLIP 분석 → Supabase DB
   ```

3. **검색 및 분석**:
   ```
   사용자 쿼리 → 백엔드 → MCP 서버들 → 결과 반환
   ```

## 🚀 확장 가능성

- **수평 확장**: 각 MCP 서버를 독립적으로 스케일링
- **새로운 MCP 서버 추가**: 새로운 기능을 위한 추가 서버
- **마이크로서비스**: 각 서버를 완전히 독립적인 서비스로 분리
- **로드 밸런싱**: 여러 인스턴스 간 부하 분산

## 🔍 모니터링

- **헬스 체크**: 각 서버의 `/health` 엔드포인트
- **로그**: Docker Compose 로그 시스템
- **메트릭**: 각 서버의 성능 지표 수집 가능

## 📝 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.
