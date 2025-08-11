FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# CLIP 설치 (사용 가능한 최신 버전)
RUN pip install --no-cache-dir torch==2.8.0 torchvision==0.23.0 ftfy regex

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 8002

# 기본 명령어 설정 (HTTP 서버 실행)
CMD ["python", "video_http_server.py"]
