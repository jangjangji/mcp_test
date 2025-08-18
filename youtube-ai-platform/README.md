# YouTube AI Platform

YouTube 동영상 분석 및 AI 채팅을 위한 플랫폼입니다.

## 🚀 시작하기

### 1. YouTube API 키 설정

이 플랫폼을 사용하려면 YouTube Data API v3 키가 필요합니다:

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. YouTube Data API v3 활성화
4. 사용자 인증 정보에서 API 키 생성
5. 생성된 API 키를 `.env` 파일에 설정:

```bash
# .env 파일 생성
cp env.example .env

# .env 파일 편집하여 실제 API 키 입력
YOUTUBE_API_KEY=your_actual_api_key_here
```

### 2. Docker Compose로 실행

```bash
# 의존성 설치 및 실행 (.env는 현재 디렉토리의 파일을 자동 사용)
docker compose up --build

# 백그라운드에서 실행
docker compose up --build -d

# 다른 위치의 .env 파일을 사용하고 싶을 때
ENV_FILE=/absolute/path/to/.env docker compose up --build -d
```

### 3. 접속

- **메인 애플리케이션**: http://localhost:3000
- **YouTube MCP 서버**: http://localhost:8001
- **Video MCP 서버**: http://localhost:8002

## 📁 프로젝트 구조

```
youtube-ai-platform/
├── backend/                 # Rust 백엔드 (포트 3000)
├── servers/
│   ├── youtube/            # YouTube MCP 서버 (포트 8001)
│   └── video/              # Video MCP 서버 (포트 8002)
├── static/                 # 프론트엔드 정적 파일
├── uploads/                # 업로드된 파일
└── docker-compose.yml      # Docker 설정
```

## 🔧 주요 기능

- **YouTube 검색**: 실제 YouTube API를 통한 동영상 검색
- **채널 분석**: 채널 정보 및 통계 분석
- **AI 채팅**: MCP 서버들과 연동된 지능형 채팅
- **비디오 분석**: 업로드된 비디오 분석

## ⚠️ 주의사항

- YouTube API 키가 설정되지 않으면 빈 결과가 반환됩니다
- YouTube Data API v3는 일일 할당량이 있으므로 과도한 사용을 피하세요
- API 키는 `.env` 파일에만 저장하고 Git에 커밋하지 마세요

## 🐛 문제 해결

### 썸네일 이미지가 표시되지 않는 경우
- YouTube API 키가 올바르게 설정되었는지 확인
- 네트워크 연결 상태 확인
- Docker 컨테이너 로그 확인: `docker-compose logs youtube-mcp-server`

### 검색 결과가 없는 경우
- YouTube API 키 설정 확인
- API 할당량 확인
- 검색어가 올바른지 확인
