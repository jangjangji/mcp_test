# 파이썬으로 MCP Agent 만들기

YouTube 검색, 요약, 채널 분석 기능을 갖춘 유튜브 에이전트를 MCP로 구현한 예제입니다.

## MCP (Model Context Protocol) 소개

- AI가 외부 데이터의 도구(Tools)에 효과적으로 연결할 수 있는 표준화된 방식
- 특히 다양한 도구의 표준화된 연결로 많이 활용되고 있음
    - **MCP Server**: 사용할 수 있는 도구(tool)를 정의하고 제공하는 역할  
    - **MCP Client**: 정의된 도구를 불러와 사용 (Claude Desktop, Cursor, OpenAI Agents SDK)
- 이번 예제에서는 유튜브 컨텐츠 분석을 위한 MCP Server를 만들어보고, OpenAI Agents SDK 기반의 MCP Client와도 연결해볼 예정입니다.

## 초기 셋팅

1. 레포지토리 clone 또는 다운로드하기
    ```bash
    git clone <your-repository-url>
    cd python_mcp_agent
    ```
2. [OpenAI 키 발급](https://platform.openai.com/api-keys)
3. [YouTube Data API Key 발급](https://console.cloud.google.com/apis/credentials)
4. .env.example를 복사한 후 API 키를 입력하고 .env로 저장

    ```bash
    cp .env.example .env
    ```

    .env 파일 내용:
    ```env
    OPENAI_API_KEY=api키_입력
    YOUTUBE_API_KEY=api_키_입력
    ```

5. [파이썬 가상환경 설정](https://docs.python.org/3/library/venv.html)
    ```bash
    python -m venv venv
    source venv/bin/activate  # Mac/Linux
    # 또는
    venv\Scripts\activate     # Windows
    ```
6. 패키지 설치

    ```bash
    pip install mcp openai-agents streamlit youtube-transcript-api python-dotenv requests
    ```

## MCP 클라이언트 연동을 위한 준비

Claude, Cursor와 같은 MCP 클라이언트 애플리케이션에서 로컬 MCP 서버를 연동하려면,  
서버 실행에 필요한 **Python 실행 파일 경로**와 **MCP 서버 스크립트 경로**를 JSON 설정에 입력해야 합니다.
- 내 경로에 알맞게 .cursor/mcp.json을 수정해둡니다.

### 경로 구성 예시

#### ✅ Windows 예시  
(예: 프로젝트 폴더가 `C:\projects\python_mcp_agent`인 경우)

> **주의:** Windows에서는 JSON 문법상 `\` 대신 `\\` (역슬래시 두 번)을 사용해야 합니다.

```json
{
  "mcpServers": {
    "mcp-test": {
      "command": "C:\\projects\\python_mcp_agent\\venv\\Scripts\\python.exe",
      "args": [
        "C:\\projects\\python_mcp_agent\\2_mcp_server.py"
      ]
    }
  }
}
```

---

#### ✅ macOS / Linux 예시  
(예: 프로젝트 폴더가 `/home/jang/mcp_test/python_mcp_agent`인 경우)

```json
{
  "mcpServers": {
    "mcp-test": {
      "command": "/home/jang/mcp_test/python_mcp_agent/venv/bin/python",
      "args": [
        "/home/jang/mcp_test/python_mcp_agent/2_mcp_server.py"
      ]
    }
  }
}
```

---

## 폴더 구조

```
python_mcp_agent/
├── 1_mcp_server_functions.ipynb   # MCP 서버 함수 예제 노트북
├── 2_mcp_server.py                # MCP 서버 구현 예제
├── 3_openai_agents_basics.py      # OpenAI Agent 기본 예제
├── 4_mcp_client.py                # Streamlit MCP Client 예제
├── .env.example                   # 환경변수 예제 파일
├── .cursor/mcp.json               # Cursor MCP 서버 설정 파일
└── README.md                      # 프로젝트 문서
```

## 사용 방법

### 1. MCP 서버 실행
```bash
source venv/bin/activate
python 2_mcp_server.py
```

### 2. Cursor에서 MCP 연동
1. Cursor 설정에서 MCP 서버 추가
2. `.cursor/mcp.json` 파일 경로 설정
3. Cursor 재시작

### 3. Streamlit 클라이언트 실행
```bash
source venv/bin/activate
streamlit run 4_mcp_client.py
```

## 주요 기능

### 1. YouTube 동영상 검색
- 키워드 기반 검색
- 최대 20개 결과
- 제목, 채널명, 조회수, 좋아요 수, 썸네일 제공

### 2. 자막 추출
- 한국어/영어 자막 우선순위
- 자동 URL 파싱
- 에러 처리 포함

### 3. 채널 분석
- 구독자 수, 총 조회수, 동영상 수
- 최근 5개 동영상 목록
- RSS 피드 활용

## 문제 해결

### MCP 서버가 인식되지 않는 경우
1. `.cursor/mcp.json` 파일 경로 확인
2. 가상환경 활성화 상태 확인
3. Cursor 재시작

### API 키 오류
1. `.env` 파일에 올바른 API 키 입력 확인
2. API 키 권한 설정 확인

### 패키지 설치 오류
```bash
pip install --upgrade pip
pip install mcp openai-agents streamlit youtube-transcript-api python-dotenv requests
```
### 클라이언트 실행 명령어
streamlit run 4_mcp_client.py

## 참고 자료

- [MCP 공식 문서](https://modelcontextprotocol.io/)
- [OpenAI Agents SDK](https://github.com/openai/openai-python)
- [YouTube Data API](https://developers.google.com/youtube/v3)

---

**참고**: 이 프로젝트는 교육 및 개발 목적으로 제작되었습니다. YouTube API 사용 시 해당 서비스의 이용약관을 준수해 주세요.
