#!/usr/bin/env python3
"""
YouTube MCP HTTP 서버 - MCP 도구를 HTTP API로 제공
"""

import asyncio
import logging
import re
import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import httpx

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# YouTube Data API 키 (환경변수에서 가져오기)
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"

# FastAPI 앱 생성
app = FastAPI(title="YouTube MCP HTTP Server", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청/응답 모델
class YouTubeSearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 5

class VideoInfoRequest(BaseModel):
    video_id: str

class ChannelAnalysisRequest(BaseModel):
    video_url: str

class MCPResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class YouTubeMCPServer:
    """YouTube 데이터 처리 MCP HTTP 서버"""
    
    def __init__(self):
        """MCP 서버 초기화"""
        logger.info("🚀 YouTube MCP HTTP 서버 시작")
        if not YOUTUBE_API_KEY:
            logger.warning("⚠️ YouTube API 키가 설정되지 않았습니다. 테스트 모드로 실행됩니다.")
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """YouTube URL에서 video_id 추출"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def _call_youtube_api(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """YouTube API 호출"""
        if not YOUTUBE_API_KEY:
            raise Exception("YouTube API 키가 설정되지 않았습니다")
        
        params['key'] = YOUTUBE_API_KEY
        url = f"{YOUTUBE_API_BASE_URL}/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    
    async def youtube_search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """YouTube 실제 검색"""
        logger.info(f"🔍 YouTube 검색: '{query}' (최대 {max_results}개)")
        
        try:
            if YOUTUBE_API_KEY:
                # 실제 YouTube API 호출
                search_params = {
                    'part': 'snippet',
                    'q': query,
                    'type': 'video',
                    'maxResults': max_results,
                    'order': 'relevance'
                }
                
                search_result = await self._call_youtube_api('search', search_params)
                
                results = []
                for item in search_result.get('items', []):
                    snippet = item['snippet']
                    video_id = item['id']['videoId']
                    
                    # 각 비디오의 상세 정보 가져오기
                    try:
                        video_info = await self.get_video_info(video_id)
                        duration = video_info.get('duration', 'N/A')
                        views = video_info.get('views', 'N/A')
                        likes = video_info.get('likes', 'N/A')
                    except Exception as e:
                        logger.warning(f"비디오 {video_id} 상세 정보 가져오기 실패: {e}")
                        duration = "N/A"
                        views = "N/A"
                        likes = "N/A"
                    
                    # 썸네일 URL 생성 (실제 YouTube 썸네일)
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                    
                    results.append({
                        "title": snippet.get('title', '제목 없음'),
                        "video_id": video_id,
                        "channel": snippet.get('channelTitle', '채널명 없음'),
                        "duration": duration,
                        "views": views,
                        "likes": likes,
                        "thumbnail": thumbnail_url,
                        "description": snippet.get('description', '')[:100] + '...' if snippet.get('description') else '',
                        "published_at": snippet.get('publishedAt', ''),
                        "channel_id": snippet.get('channelId', '')
                    })
                
                logger.info(f"✅ 실제 YouTube 검색 완료: {len(results)}개 결과")
                return {
                    "query": query,
                    "max_results": max_results,
                    "results": results,
                    "total_count": len(results)
                }
            else:
                # API 키가 없으면 빈 결과 반환
                logger.warning("⚠️ YouTube API 키가 없어 빈 결과를 반환합니다")
                return {
                    "query": query,
                    "max_results": max_results,
                    "results": [],
                    "total_count": 0
                }
                
        except Exception as e:
            logger.error(f"YouTube 검색 오류: {e}")
            # 오류 시 빈 결과 반환
            return {
                "query": query,
                "max_results": max_results,
                "results": [],
                "total_count": 0
            }
    
    async def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """동영상 정보 가져오기"""
        logger.info(f"📹 동영상 정보 조회: {video_id}")
        
        try:
            if YOUTUBE_API_KEY:
                # 실제 YouTube API 호출
                video_params = {
                    'part': 'snippet,statistics,contentDetails',
                    'id': video_id
                }
                
                video_result = await self._call_youtube_api('videos', video_params)
                
                if not video_result.get('items'):
                    raise Exception("동영상을 찾을 수 없습니다")
                
                item = video_result['items'][0]
                snippet = item['snippet']
                statistics = item.get('statistics', {})
                content_details = item.get('contentDetails', {})
                
                # 썸네일 URL 생성
                thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                
                return {
                    "video_id": video_id,
                    "title": snippet.get('title', '제목 없음'),
                    "description": snippet.get('description', '설명 없음'),
                    "duration": content_details.get('duration', 'N/A'),
                    "views": statistics.get('viewCount', 'N/A'),
                    "likes": statistics.get('likeCount', 'N/A'),
                    "channel": snippet.get('channelTitle', '채널명 없음'),
                    "channel_id": snippet.get('channelId', 'N/A'),  # 채널 ID 추가
                    "upload_date": snippet.get('publishedAt', 'N/A'),
                    "category": snippet.get('categoryId', 'N/A'),
                    "thumbnail": thumbnail_url
                }
            else:
                # API 키가 없으면 기본 정보만 반환
                return {
                    "video_id": video_id,
                    "title": "YouTube API 키가 필요합니다",
                    "description": "YouTube Data API 키를 설정해주세요",
                    "duration": "N/A",
                    "views": "N/A",
                    "likes": "N/A",
                    "channel": "N/A",
                    "upload_date": "N/A",
                    "category": "N/A",
                    "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                }
                
        except Exception as e:
            logger.error(f"동영상 정보 조회 오류: {e}")
            return {
                "video_id": video_id,
                "title": "오류 발생",
                "description": str(e),
                "duration": "N/A",
                "views": "N/A",
                "likes": "N/A",
                "channel": "N/A",
                "upload_date": "N/A",
                "category": "N/A",
                "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            }
    
    async def analyze_channel(self, video_url: str) -> Dict[str, Any]:
        """채널 분석"""
        logger.info(f"📊 채널 분석 시작: {video_url}")
        
        # video_id 추출
        video_id = self._extract_video_id(video_url)
        if not video_id:
            raise HTTPException(status_code=400, detail="유효하지 않은 YouTube URL입니다")
        
        try:
            if YOUTUBE_API_KEY:
                # 동영상 정보로부터 채널 ID 가져오기
                video_info = await self.get_video_info(video_id)
                channel_id = video_info.get('channel_id')
                
                if channel_id:
                    # 채널 정보 API 호출
                    channel_params = {
                        'part': 'snippet,statistics,brandingSettings',
                        'id': channel_id
                    }
                    
                    channel_result = await self._call_youtube_api('channels', channel_params)
                    
                    if channel_result.get('items'):
                        channel = channel_result['items'][0]
                        snippet = channel['snippet']
                        statistics = channel.get('statistics', {})
                        branding = channel.get('brandingSettings', {})
                        
                        return {
                            "video_id": video_id,
                            "channel_name": snippet.get('title', '채널명 없음'),
                            "subscriber_count": statistics.get('subscriberCount', 'N/A'),
                            "total_videos": statistics.get('videoCount', 'N/A'),
                            "total_views": statistics.get('viewCount', 'N/A'),
                            "channel_description": snippet.get('description', '설명 없음'),
                            "channel_created": snippet.get('publishedAt', 'N/A'),
                            "category": snippet.get('categoryId', 'N/A'),
                            "country": snippet.get('country', 'N/A'),
                            "recent_videos": []  # 별도 API 호출 필요
                        }
                
                # 채널 정보를 가져올 수 없는 경우 기본 정보 반환
                return {
                    "video_id": video_id,
                    "channel_name": video_info.get('channel', '채널명 없음'),
                    "subscriber_count": "N/A",
                    "total_videos": "N/A", 
                    "total_views": "N/A",
                    "channel_description": "채널 정보를 가져올 수 없습니다",
                    "channel_created": "N/A",
                    "category": "N/A",
                    "country": "N/A",
                    "recent_videos": []
                }
            else:
                # API 키가 없으면 기본 정보만 반환
                return {
                    "video_id": video_id,
                    "channel_name": "YouTube API 키가 필요합니다",
                    "subscriber_count": "N/A",
                    "total_videos": "N/A",
                    "total_views": "N/A", 
                    "channel_description": "YouTube Data API 키를 설정해주세요",
                    "channel_created": "N/A",
                    "category": "N/A",
                    "country": "N/A",
                    "recent_videos": []
                }
                
        except Exception as e:
            logger.error(f"채널 분석 오류: {e}")
            return {
                "video_id": video_id,
                "channel_name": "오류 발생",
                "subscriber_count": "N/A",
                "total_videos": "N/A",
                "total_views": "N/A",
                "channel_description": str(e),
                "channel_created": "N/A",
                "category": "N/A",
                "country": "N/A",
                "recent_videos": []
            }

# MCP 서버 인스턴스 생성
mcp_server = YouTubeMCPServer()

# API 엔드포인트들
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "YouTube MCP HTTP Server", "status": "running"}

@app.get("/tools")
async def list_tools():
    """사용 가능한 MCP 도구 목록 반환"""
    tools = [
        {
            "name": "youtube_search",
            "description": "YouTube에서 동영상을 검색합니다",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색할 키워드"},
                    "max_results": {"type": "integer", "description": "최대 결과 수", "default": 5}
                },
                "required": ["query"]
            }
        },
        {
            "name": "get_video_info",
            "description": "YouTube 동영상의 상세 정보를 가져옵니다",
            "input_schema": {
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "YouTube 동영상 ID"}
                },
                "required": ["video_id"]
            }
        },
        {
            "name": "analyze_channel",
            "description": "YouTube 채널의 상세 정보를 분석합니다",
            "input_schema": {
                "type": "object",
                "properties": {
                    "video_url": {"type": "string", "description": "YouTube 동영상 URL"}
                },
                "required": ["video_url"]
            }
        }
    ]
    
    return {"tools": tools, "total": len(tools)}

@app.post("/tools/youtube_search")
async def youtube_search_tool(request: YouTubeSearchRequest):
    """YouTube 검색 MCP 도구"""
    try:
        result = await mcp_server.youtube_search(request.query, request.max_results)
        return MCPResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"YouTube 검색 오류: {e}")
        return MCPResponse(success=False, error=str(e))

@app.post("/tools/get_video_info")
async def get_video_info_tool(request: VideoInfoRequest):
    """동영상 정보 가져오기 MCP 도구"""
    try:
        result = await mcp_server.get_video_info(request.video_id)
        return MCPResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"동영상 정보 조회 오류: {e}")
        return MCPResponse(success=False, error=str(e))

@app.post("/tools/analyze_channel")
async def analyze_channel_tool(request: ChannelAnalysisRequest):
    """채널 분석 MCP 도구"""
    try:
        result = await mcp_server.analyze_channel(request.video_url)
        return MCPResponse(success=True, data=result)
    except Exception as e:
        logger.error(f"채널 분석 오류: {e}")
        return MCPResponse(success=False, error=str(e))

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "service": "youtube-mcp-http-server"}

if __name__ == "__main__":
    """메인 실행"""
    logger.info("🚀 YouTube MCP HTTP 서버 시작 중...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001, 
        log_level="info"
    )
