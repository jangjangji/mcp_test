#!/usr/bin/env python3
"""
YouTube AI Platform - YouTube 전용 MCP 서버
YouTube 데이터 처리 및 분석 기능을 제공하는 MCP 서버
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel import NotificationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
)
import os
import sys
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 환경 변수 로드
load_dotenv()

# Supabase 클라이언트 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="YouTube MCP Server", version="1.0.0")

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

class YouTubeMCPServer:
    """YouTube 데이터 처리 전용 MCP 서버"""
    
    def __init__(self):
        self.server = Server("youtube-mcp-server")
        self.setup_handlers()
        
    def setup_handlers(self):
        """MCP 서버 핸들러 설정"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """사용 가능한 도구 목록 반환"""
            tools = [
                Tool(
                    name="youtube_search",
                    description="YouTube에서 비디오를 검색합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "검색할 키워드"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "최대 결과 수",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="youtube_get_video_info",
                    description="YouTube 비디오의 상세 정보를 가져옵니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_id": {
                                "type": "string",
                                "description": "YouTube 비디오 ID"
                            }
                        },
                        "required": ["video_id"]
                    }
                ),
                Tool(
                    name="youtube_get_channel_info",
                    description="YouTube 채널 정보를 가져옵니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "channel_id": {
                                "type": "string",
                                "description": "YouTube 채널 ID"
                            }
                        },
                        "required": ["channel_id"]
                    }
                ),
                Tool(
                    name="youtube_get_comments",
                    description="YouTube 비디오 댓글을 가져옵니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_id": {
                                "type": "string",
                                "description": "YouTube 비디오 ID"
                            },
                            "max_comments": {
                                "type": "integer",
                                "description": "최대 댓글 수",
                                "default": 50
                            }
                        },
                        "required": ["video_id"]
                    }
                ),
                Tool(
                    name="youtube_analyze_trending",
                    description="YouTube 트렌딩 분석을 수행합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "region": {
                                "type": "string",
                                "description": "지역 코드 (예: KR, US)",
                                "default": "KR"
                            },
                            "category": {
                                "type": "string",
                                "description": "카테고리 (예: all, music, gaming)",
                                "default": "all"
                            }
                        }
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """도구 호출 처리"""
            try:
                if name == "youtube_search":
                    return await self.youtube_search(arguments)
                elif name == "youtube_get_video_info":
                    return await self.youtube_get_video_info(arguments)
                elif name == "youtube_get_channel_info":
                    return await self.youtube_get_channel_info(arguments)
                elif name == "youtube_get_comments":
                    return await self.youtube_get_comments(arguments)
                elif name == "youtube_analyze_trending":
                    return await self.youtube_analyze_trending(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Tool call error: {str(e)}")
                raise ValueError(f"Tool execution failed: {str(e)}")
    
    async def youtube_search(self, arguments: Dict[str, Any]) -> CallToolResult:
        """YouTube 비디오 검색 - MCP 툴"""
        try:
            query = arguments.get("query", "")
            max_results = arguments.get("max_results", 10)
            
            logger.info(f"youtube_search MCP 툴 실행: query={query}, max_results={max_results}")
            
            # 실제 검색 결과 형식으로 반환 (프론트엔드 호환)
            results = [
                {
                    "title": f"{query} 요리 영상 {i}",
                    "channel": f"요리 채널 {i}",
                    "views": f"{10000 * i:,}",
                    "likes": f"{1000 * i:,}",
                    "thumbnail": f"https://example.com/thumbnail_{i}.jpg",
                    "video_id": f"video_{i}",
                    "duration": f"{i * 2}:30",
                    "published": "2024-01-15"
                }
                for i in range(1, min(max_results + 1, 6))
            ]
            
            logger.info(f"검색 결과 생성 완료: {len(results)}개")
            
            # 프론트엔드가 기대하는 형식으로 반환
            content = [
                {
                    "type": "text",
                    "text": json.dumps({
                        "query": query,
                        "results": results,
                        "total_count": len(results)
                    }, ensure_ascii=False)
                }
            ]
            
            logger.info(f"MCP 툴 응답 생성 완료")
            return CallToolResult(content=content)
            
        except Exception as e:
            logger.error(f"youtube_search MCP 툴 실행 오류: {e}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
            
            # 오류 발생 시 기본 응답 반환
            error_content = [
                {
                    "type": "text",
                    "text": json.dumps({
                        "query": arguments.get("query", ""),
                        "results": [],
                        "total_count": 0,
                        "error": str(e)
                    }, ensure_ascii=False)
                }
            ]
            return CallToolResult(content=error_content)
    
    async def youtube_get_video_info(self, arguments: Dict[str, Any]) -> CallToolResult:
        """YouTube 비디오 정보 가져오기"""
        video_id = arguments.get("video_id", "")
        
        # 시뮬레이션 비디오 정보
        video_info = {
            "title": f"비디오 제목: {video_id}",
            "description": "이것은 샘플 비디오 설명입니다.",
            "channel": "샘플 채널",
            "duration": "5:30",
            "views": "1,234,567",
            "likes": "12,345",
            "published": "2024-01-15"
        }
        
        content = [
            {
                "type": "text",
                "text": f"비디오 정보:\n" +
                       f"제목: {video_info['title']}\n" +
                       f"채널: {video_info['channel']}\n" +
                       f"길이: {video_info['duration']}\n" +
                       f"조회수: {video_info['views']}\n" +
                       f"좋아요: {video_info['likes']}\n" +
                       f"업로드: {video_info['published']}"
            }
        ]
        
        return CallToolResult(content=content)
    
    async def youtube_get_channel_info(self, arguments: Dict[str, Any]) -> CallToolResult:
        """YouTube 채널 정보 가져오기"""
        channel_id = arguments.get("channel_id", "")
        
        # 시뮬레이션 채널 정보
        channel_info = {
            "name": f"채널 이름: {channel_id}",
            "subscribers": "123,456",
            "videos": "456",
            "description": "이것은 샘플 채널 설명입니다.",
            "created_at": "2020-01-01"
        }
        
        content = [
            {
                "type": "text",
                "text": f"채널 정보:\n" +
                       f"이름: {channel_info['name']}\n" +
                       f"구독자: {channel_info['subscribers']}\n" +
                       f"비디오 수: {channel_info['videos']}\n" +
                       f"설명: {channel_info['description']}\n" +
                       f"생성일: {channel_info['created_at']}"
            }
        ]
        
        return CallToolResult(content=content)
    
    async def youtube_get_comments(self, arguments: Dict[str, Any]) -> CallToolResult:
        """YouTube 댓글 가져오기"""
        video_id = arguments.get("video_id", "")
        max_comments = arguments.get("max_comments", 50)
        
        # 시뮬레이션 댓글
        comments = [
            {
                "author": f"사용자{i}",
                "text": f"이것은 댓글 {i}입니다. 정말 좋은 비디오네요!",
                "likes": i * 10,
                "date": "2024-01-15"
            }
            for i in range(1, min(max_comments + 1, 6))
        ]
        
        content = [
            {
                "type": "text",
                "text": f"댓글 ({len(comments)}개):\n\n" +
                       "\n".join([
                           f"• {c['author']}: {c['text']} (좋아요: {c['likes']})"
                           for c in comments
                       ])
            }
        ]
        
        return CallToolResult(content=content)
    
    async def youtube_analyze_trending(self, arguments: Dict[str, Any]) -> CallToolResult:
        """YouTube 트렌딩 분석"""
        region = arguments.get("region", "KR")
        category = arguments.get("category", "all")
        
        # 시뮬레이션 트렌딩 데이터
        trending_videos = [
            {
                "title": f"트렌딩 비디오 {i}",
                "channel": f"인기 채널 {i}",
                "views": f"{1000000 * i:,}",
                "category": category
            }
            for i in range(1, 6)
        ]
        
        content = [
            {
                "type": "text",
                "text": f"{region} 지역 {category} 카테고리 트렌딩:\n\n" +
                       "\n".join([
                           f"• {v['title']} - {v['channel']} (조회수: {v['views']})"
                           for v in trending_videos
                       ])
            }
        ]
        
        return CallToolResult(content=content)

# YouTube MCP 서버 인스턴스 생성
youtube_server = YouTubeMCPServer()

# HTTP 엔드포인트들
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "YouTube MCP Server", "status": "running"}

@app.get("/tools")
async def list_tools():
    """사용 가능한 도구 목록 반환"""
    try:
        # MCP 서버 대신 직접 tool 목록 반환
        tools = [
            {
                "name": "youtube_search",
                "description": "YouTube에서 비디오를 검색합니다"
            },
            {
                "name": "youtube_get_video_info", 
                "description": "YouTube 비디오의 상세 정보를 가져옵니다"
            },
            {
                "name": "youtube_get_channel_info",
                "description": "YouTube 채널 정보를 가져옵니다"
            },
            {
                "name": "youtube_get_comments",
                "description": "YouTube 비디오 댓글을 가져옵니다"
            },
            {
                "name": "youtube_analyze_trending",
                "description": "YouTube 트렌딩 분석을 수행합니다"
            }
        ]
        return {"tools": tools}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/youtube_search")
async def youtube_search_endpoint(request: Dict[str, Any]):
    """YouTube 검색 엔드포인트 - MCP 툴 사용"""
    try:
        logger.info(f"youtube_search 요청 받음: {request}")
        
        # MCP 툴 호출: youtube_search
        result = await youtube_server.youtube_search(request)
        logger.info(f"MCP 툴 결과: {result}")
        
        # MCP 툴 결과에서 실제 데이터 추출
        if result.content and len(result.content) > 0:
            first_content = result.content[0]
            logger.info(f"첫 번째 content: {first_content}")
            
            # TextContent 객체의 속성에 직접 접근
            if hasattr(first_content, 'type') and first_content.type == 'text':
                try:
                    # JSON 문자열을 파싱하여 실제 데이터 추출
                    text_content = first_content.text
                    logger.info(f"텍스트 content: {text_content}")
                    
                    parsed_data = json.loads(text_content)
                    logger.info(f"파싱된 데이터: {parsed_data}")
                    
                    if "results" in parsed_data:
                        # 프론트엔드가 기대하는 형식으로 변환
                        response_data = {
                            "success": True,
                            "data": parsed_data["results"],
                            "error": None
                        }
                        logger.info(f"응답 데이터: {response_data}")
                        return response_data
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 파싱 오류: {e}, 텍스트: {text_content}")
                except Exception as e:
                    logger.error(f"데이터 처리 오류: {e}")
        
        # MCP 툴 실패 시 기본 응답 반환
        logger.warning("MCP 툴 실패, 기본 응답 반환")
        return {
            "success": True,
            "data": [],
            "error": "MCP 툴 실행 실패"
        }
        
    except Exception as e:
        logger.error(f"youtube_search 엔드포인트 오류: {e}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
        
        # 오류 발생 시에도 기본 응답 반환
        return {
            "success": False,
            "data": [],
            "error": str(e)
        }

@app.post("/youtube_get_video_info")
async def youtube_get_video_info_endpoint(request: Dict[str, Any]):
    """YouTube 비디오 정보 엔드포인트 - MCP 툴 호출"""
    try:
        # MCP 툴 호출: youtube_get_video_info
        result = await youtube_server.youtube_get_video_info(request)
        return {"result": result.content}
    except Exception as e:
        logger.error(f"youtube_get_video_info MCP 툴 호출 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/youtube_get_channel_info")
async def youtube_get_channel_info_endpoint(request: Dict[str, Any]):
    """YouTube 채널 정보 엔드포인트 - MCP 툴 호출"""
    try:
        # MCP 툴 호출: youtube_get_channel_info
        result = await youtube_server.youtube_get_channel_info(request)
        return {"result": result.content}
    except Exception as e:
        logger.error(f"youtube_get_channel_info MCP 툴 호출 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/youtube_get_comments")
async def youtube_get_comments_endpoint(request: Dict[str, Any]):
    """YouTube 댓글 엔드포인트 - MCP 툴 호출"""
    try:
        # MCP 툴 호출: youtube_get_comments
        result = await youtube_server.youtube_get_comments(request)
        return {"result": result.content}
    except Exception as e:
        logger.error(f"youtube_get_comments MCP 툴 호출 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/youtube_analyze_trending")
async def youtube_analyze_trending_endpoint(request: Dict[str, Any]):
    """YouTube 트렌딩 분석 엔드포인트 - MCP 툴 호출"""
    try:
        # MCP 툴 호출: youtube_analyze_trending
        result = await youtube_server.youtube_analyze_trending(request)
        return {"result": result.content}
    except Exception as e:
        logger.error(f"youtube_analyze_trending MCP 툴 호출 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    """메인 함수"""
    logger.info("🚀 YouTube MCP HTTP 서버 시작 중...")
    
    # HTTP 서버 실행
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
