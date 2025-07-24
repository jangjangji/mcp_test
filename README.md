# YouTube Search API with MCP Agent

YouTube 검색 및 유사도 검색을 위한 통합 시스템입니다. Rust 백엔드, Python MCP 서버, 그리고 모던 웹 UI를 포함합니다.

## 📁 프로젝트 구조

```
python_mcp_agent/
├── youtube-search-api/          # Rust 백엔드 서버
│   ├── src/
│   │   └── main.rs             # Rust 서버 메인 코드
│   ├── static/
│   │   ├── index.html          # 웹 UI
│   │   └── app.js             # 프론트엔드 JavaScript
│   ├── my_mcp_client.py       # Rust-Python 연동 클라이언트
│   ├── transcript_helper.py    # 자막 처리 헬퍼
│   └── Cargo.toml             # Rust 의존성
├── mcp_server.py               # Python MCP 서버 (핵심 로직)
├── requirements.txt            # Python 의존성
├── mcp.json                   # MCP 설정
└── venv/                      # Python 가상환경
```

## 🚀 주요 기능

### 1. **유사도 검색** (Similarity Search)
- OpenAI 임베딩을 사용한 텍스트 유사도 검색
- Supabase 벡터 데이터베이스에서 유사한 자막 청크 검색
- 가장 관련성 높은 YouTube 영상 추천

### 2. **YouTube 검색** (YouTube Search)
- YouTube Data API v3를 통한 실시간 영상 검색
- 제목, 채널명, 조회수, 좋아요 수 등 상세 정보 제공
- 한국어 검색어 지원

### 3. **채널 정보** (Channel Info)
- YouTube 영상 URL로부터 채널 정보 추출
- 최근 5개 영상 목록 제공
- 채널 통계 정보 표시

### 4. **자막 가져오기** (Get Subtitles)
- YouTube 영상의 자막 자동 추출
- 한국어/영어 자막 지원
- 텍스트 형태로 변환

### 5. **채널 저장** (Save Channel)
- 채널의 모든 영상 자막을 자동 수집
- 300자씩 청킹하여 임베딩 생성
- Supabase 벡터 데이터베이스에 저장

## 🛠️ 기술 스택

### **백엔드**
- **Rust**: Actix Web, async/await, anyhow
- **Python**: FastMCP, OpenAI, Supabase, YouTube API
- **데이터베이스**: Supabase (PostgreSQL + 벡터 검색)

### **프론트엔드**
- **HTML/CSS**: Bootstrap 5, Font Awesome
- **JavaScript**: Fetch API, JSON 처리
- **UI/UX**: 모던 디자인, 로딩 상태, 에러 처리

## 🔧 설치 및 실행

### 1. **의존성 설치**
```bash
# Python 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# Python 의존성 설치
pip install -r requirements.txt

# Rust 의존성 설치
cd youtube-search-api
cargo build
```

### 2. **환경 변수 설정**
```bash
# .env 파일 생성
cp youtube-search-api/env.example .env

# 필요한 API 키 설정
YOUTUBE_API_KEY=your_youtube_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_api_key
```

### 3. **서버 실행**
```bash
# Rust 서버 실행
cd youtube-search-api
cargo run
```

서버가 `http://127.0.0.1:8080`에서 실행됩니다.

## 📊 API 엔드포인트

### **1. 유사도 검색**
```
POST /api/search-similar
Body: {"query": "검색어"}
```

### **2. YouTube 검색**
```
POST /api/search-youtube  
Body: {"query": "검색어"}
```

### **3. 채널 정보**
```
POST /api/channel-info
Body: {"video_url": "유튜브 URL"}
```

### **4. 자막 가져오기**
```
POST /api/transcript
Body: {"url": "유튜브 URL"}
```

### **5. 채널 저장**
```
POST /api/save-channel
Body: {"channel_id": "채널 ID"}
```

## 🔄 데이터 흐름

### **YouTube 검색 예시 ("제육볶음")**
```
1. 프론트엔드 → Rust API → Python MCP → YouTube API
2. YouTube API → Python MCP → Rust API → 프론트엔드
3. 결과: 관련 YouTube 영상 목록 표시
```

### **유사도 검색 예시**
```
1. 프론트엔드 → Rust API → Python MCP → OpenAI 임베딩
2. OpenAI → Python MCP → Supabase 벡터 검색
3. Supabase → Python MCP → Rust API → 프론트엔드
4. 결과: 가장 유사한 영상 정보 표시
```

## 🎯 핵심 특징

- **비동기 처리**: Rust async/await로 고성능 처리
- **모듈화**: Rust 백엔드 + Python MCP 서버 분리
- **벡터 검색**: OpenAI 임베딩 + Supabase 벡터 DB
- **실시간 검색**: YouTube Data API v3 실시간 연동
- **모던 UI**: Bootstrap 5 기반 반응형 디자인
- **에러 처리**: 각 단계별 안정적인 에러 처리

## 📝 개발 노트

- Python MCP 서버가 핵심 비즈니스 로직 담당
- Rust 백엔드는 API 라우팅 및 Python 연동
- 프론트엔드는 순수 HTML/JS로 구현
- 모든 통신은 JSON 형태로 처리
