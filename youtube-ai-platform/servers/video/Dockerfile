FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치 (최소한으로)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY requirements.txt .

# pip 업그레이드 및 패키지 설치
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --timeout 600 --retries 5 --default-timeout 600 -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 8002

# 기본 명령어 설정 (MCP 서버 실행)
CMD ["python", "video_mcp_server.py"]
