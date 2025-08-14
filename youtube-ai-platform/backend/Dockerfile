FROM rust:1.82-slim as builder

# 시스템 패키지 설치 (OpenSSL 개발 패키지 포함)
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Cargo.toml과 src 디렉토리, static 디렉토리 복사
COPY backend/Cargo.toml ./
COPY backend/src ./src
COPY backend/static ./static

# 애플리케이션 빌드
RUN cargo build --release

# 런타임 이미지
FROM debian:bookworm-slim

# Python과 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    ca-certificates \
    libssl3 \
    git \
    && rm -rf /var/lib/apt/lists/*

# 사용자 생성
RUN useradd -m -u 1000 appuser

# 작업 디렉토리 설정
WORKDIR /app

# 빌더에서 바이너리 복사
COPY --from=builder /app/target/release/youtube-search-api /app/youtube-search-api

# static 디렉토리 복사
COPY --from=builder /app/static /app/static

# MCP 서버 코드 복사
COPY servers/youtube /app/youtube
COPY servers/video /app/video

# Python 가상환경 생성 및 MCP 의존성 설치
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# requirements.txt 복사 및 설치
RUN pip install --upgrade pip && \
    pip install -r /app/youtube/requirements.txt && \
    pip install -r /app/video/requirements.txt

# 업로드 디렉토리 생성
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app

# 사용자 변경
USER appuser

# 포트 노출
EXPOSE 8080

# 애플리케이션 실행
CMD ["./youtube-search-api"]
