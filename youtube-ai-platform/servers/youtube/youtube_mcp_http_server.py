#!/usr/bin/env python3
"""
YouTube AI Platform - YouTube MCP HTTP 래퍼 서버
YouTube MCP 서버를 HTTP API로 래핑하여 외부에서 접근 가능하게 함
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
from datetime import datetime
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="YouTube MCP HTTP Server",
    description="YouTube 데이터 처리 MCP 서버의 HTTP 래퍼",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델들
class YouTubeSearchRequest(BaseModel):
    query: str
    max_results: int = 10

class VideoInfoRequest(BaseModel):
    video_id: str

class ChannelInfoRequest(BaseModel):
    channel_id: str

class CommentsRequest(BaseModel):
    video_id: str
    max_comments: int = 50

class TrendingRequest(BaseModel):
    region: str = "KR"
    category: str = "all"

class YouTubeSearchResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    message: str

class VideoInfoResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: str

class ChannelInfoResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: str

class CommentsResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    message: str

class TrendingResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    message: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    server: str

class YouTubeMCPServer:
    """YouTube MCP 서버 시뮬레이션"""
    
    def __init__(self):
        self.server_name = "youtube-mcp-server"
    
    async def youtube_search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """YouTube 비디오 검색 시뮬레이션"""
        results = [
            {
                "video_id": f"video_{i}",
                "title": f"검색 결과 {i}: {query}",
                "channel": f"채널 {i}",
                "views": f"{1000 * i:,}",
                "duration": "10:30",
                "published_at": "2024-01-01",
                "thumbnail": f"https://example.com/thumb_{i}.jpg"
            }
            for i in range(1, min(max_results + 1, 6))
        ]
        return results
    
    async def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """YouTube 비디오 상세 정보 시뮬레이션"""
        video_info = {
            "video_id": video_id,
            "title": f"샘플 비디오: {video_id}",
            "description": "이것은 샘플 비디오 설명입니다.",
            "channel": "샘플 채널",
            "channel_id": "UC_sample",
            "views": "1,234,567",
            "likes": "12,345",
            "duration": "15:30",
            "published_at": "2024-01-15",
            "tags": ["태그1", "태그2", "태그3"],
            "thumbnail": "https://example.com/thumb.jpg"
        }
        return video_info
    
    async def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """YouTube 채널 정보 시뮬레이션"""
        channel_info = {
            "channel_id": channel_id,
            "name": f"샘플 채널: {channel_id}",
            "subscribers": "1,234,567",
            "videos": "456",
            "description": "이것은 샘플 채널 설명입니다.",
            "created_at": "2020-01-01",
            "avatar": "https://example.com/avatar.jpg"
        }
        return channel_info
    
    async def get_comments(self, video_id: str, max_comments: int = 50) -> List[Dict[str, Any]]:
        """YouTube 댓글 시뮬레이션"""
        comments = [
            {
                "comment_id": f"comment_{i}",
                "author": f"사용자{i}",
                "text": f"이것은 댓글 {i}입니다. 정말 좋은 비디오네요!",
                "likes": i * 10,
                "date": "2024-01-15",
                "author_avatar": f"https://example.com/user_{i}.jpg"
            }
            for i in range(1, min(max_comments + 1, 6))
        ]
        return comments
    
    async def analyze_trending(self, region: str = "KR", category: str = "all") -> List[Dict[str, Any]]:
        """YouTube 트렌딩 분석 시뮬레이션"""
        trending_videos = [
            {
                "video_id": f"trending_{i}",
                "title": f"트렌딩 비디오 {i}",
                "channel": f"인기 채널 {i}",
                "views": f"{1000000 * i:,}",
                "category": category,
                "thumbnail": f"https://example.com/trending_{i}.jpg"
            }
            for i in range(1, 6)
        ]
        return trending_videos

# YouTube MCP 서버 인스턴스 생성
youtube_server = YouTubeMCPServer()

# API 엔드포인트들
@app.get("/", response_model=HealthResponse)
async def root():
    """루트 엔드포인트 - 서버 상태 확인"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        server="youtube-mcp-server"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크 엔드포인트"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        server="youtube-mcp-server"
    )

@app.post("/youtube/search", response_model=YouTubeSearchResponse)
async def youtube_search(request: YouTubeSearchRequest):
    """YouTube 비디오 검색"""
    try:
        results = await youtube_server.youtube_search(request.query, request.max_results)
        return YouTubeSearchResponse(
            success=True,
            data=results,
            message=f"'{request.query}' 검색 완료"
        )
    except Exception as e:
        logger.error(f"YouTube 검색 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")

@app.post("/youtube/video/info", response_model=VideoInfoResponse)
async def get_video_info(request: VideoInfoRequest):
    """YouTube 비디오 상세 정보"""
    try:
        video_info = await youtube_server.get_video_info(request.video_id)
        return VideoInfoResponse(
            success=True,
            data=video_info,
            message="비디오 정보 조회 완료"
        )
    except Exception as e:
        logger.error(f"비디오 정보 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"비디오 정보 조회 중 오류 발생: {str(e)}")

@app.post("/youtube/channel/info", response_model=ChannelInfoResponse)
async def get_channel_info(request: ChannelInfoRequest):
    """YouTube 채널 정보"""
    try:
        channel_info = await youtube_server.get_channel_info(request.channel_id)
        return ChannelInfoResponse(
            success=True,
            data=channel_info,
            message="채널 정보 조회 완료"
        )
    except Exception as e:
        logger.error(f"채널 정보 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"채널 정보 조회 중 오류 발생: {str(e)}")

@app.post("/youtube/comments", response_model=CommentsResponse)
async def get_comments(request: CommentsRequest):
    """YouTube 댓글 가져오기"""
    try:
        comments = await youtube_server.get_comments(request.video_id, request.max_comments)
        return CommentsResponse(
            success=True,
            data=comments,
            message="댓글 조회 완료"
        )
    except Exception as e:
        logger.error(f"댓글 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"댓글 조회 중 오류 발생: {str(e)}")

@app.post("/youtube/trending", response_model=TrendingResponse)
async def analyze_trending(request: TrendingRequest):
    """YouTube 트렌딩 분석"""
    try:
        trending_videos = await youtube_server.analyze_trending(request.region, request.category)
        return TrendingResponse(
            success=True,
            data=trending_videos,
            message=f"{request.region} 지역 {request.category} 카테고리 트렌딩 분석 완료"
        )
    except Exception as e:
        logger.error(f"트렌딩 분석 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"트렌딩 분석 중 오류 발생: {str(e)}")

@app.get("/tools")
async def list_tools():
    """사용 가능한 도구 목록"""
    tools = [
        {
            "name": "youtube_search",
            "description": "YouTube에서 비디오를 검색합니다",
            "endpoint": "/youtube/search",
            "method": "POST"
        },
        {
            "name": "get_video_info",
            "description": "YouTube 비디오의 상세 정보를 가져옵니다",
            "endpoint": "/youtube/video/info",
            "method": "POST"
        },
        {
            "name": "get_channel_info",
            "description": "YouTube 채널 정보를 가져옵니다",
            "endpoint": "/youtube/channel/info",
            "method": "POST"
        },
        {
            "name": "get_comments",
            "description": "YouTube 비디오의 댓글을 가져옵니다",
            "endpoint": "/youtube/comments",
            "method": "POST"
        },
        {
            "name": "analyze_trending",
            "description": "YouTube 트렌딩 비디오를 분석합니다",
            "endpoint": "/youtube/trending",
            "method": "POST"
        }
    ]
    return {"tools": tools}

if __name__ == "__main__":
    # 서버 실행
    port = int(os.getenv("YOUTUBE_MCP_PORT", 8001))
    host = os.getenv("YOUTUBE_MCP_HOST", "0.0.0.0")
    
    logger.info(f"🚀 YouTube MCP HTTP 서버 시작 중... (포트: {port})")
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
