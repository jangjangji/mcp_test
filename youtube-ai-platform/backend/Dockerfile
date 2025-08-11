FROM rust:1.82-slim as builder

# 시스템 패키지 설치 (OpenSSL 개발 패키지 포함)
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Cargo.toml과 src 디렉토리, static 디렉토리 복사
COPY Cargo.toml ./
COPY src ./src
COPY static ./static

# 애플리케이션 빌드
RUN cargo build --release

# 런타임 이미지
FROM debian:bookworm-slim

# 필요한 런타임 라이브러리 설치
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# 사용자 생성
RUN useradd -m -u 1000 appuser

# 작업 디렉토리 설정
WORKDIR /app

# 빌더에서 바이너리 복사 (실제 패키지 이름 사용)
COPY --from=builder /app/target/release/youtube-search-api /app/youtube-search-api

# static 디렉토리도 복사
COPY --from=builder /app/static /app/static

# 업로드 디렉토리 생성
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app

# 사용자 변경
USER appuser

# 포트 노출
EXPOSE 3000

# 애플리케이션 실행
CMD ["./youtube-search-api"]
