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
from mcp.server.stdio import stdio_server
from mcp import types
from mcp.shared.exceptions import McpError
import os
import sys
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Supabase 클라이언트 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수가 설정된 경우에만 Supabase 클라이언트 생성
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase: Client = None
    logger.warning("Supabase 환경 변수가 설정되지 않았습니다. Supabase 기능이 비활성화됩니다.")

class YouTubeMCPServer:
    """YouTube 데이터 처리 전용 MCP 서버"""
    
    def __init__(self):
        self.server = Server("youtube-mcp-server")
        self.setup_handlers()
        
    def setup_handlers(self):
        """MCP 서버 핸들러 설정"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> types.ListToolsResult:
            """사용 가능한 도구 목록 반환"""
            tools = [
                types.Tool(
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
                types.Tool(
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
                types.Tool(
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
                types.Tool(
                    name="youtube_get_comments",
                    description="YouTube 비디오의 댓글을 가져옵니다",
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
                types.Tool(
                    name="youtube_analyze_trending",
                    description="YouTube 트렌딩 비디오를 분석합니다",
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
                                "description": "카테고리 (예: music, gaming, news)",
                                "default": "all"
                            }
                        }
                    }
                )
            ]
            return types.ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> types.CallToolResult:
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
                    raise Error(
                        code=ErrorCode.INVALID_ARGUMENT,
                        message=f"Unknown tool: {name}"
                    )
            except Exception as e:
                logger.error(f"Tool call error: {str(e)}")
                raise Error(
                    code=ErrorCode.INTERNAL_ERROR,
                    message=f"Tool execution failed: {str(e)}"
                )
    
    async def youtube_search(self, arguments: Dict[str, Any]) -> types.CallToolResult:
        """YouTube 비디오 검색"""
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 10)
        
        # 실제 YouTube API 호출 대신 시뮬레이션
        results = [
            {
                "video_id": f"video_{i}",
                "title": f"검색 결과 {i}: {query}",
                "channel": f"채널 {i}",
                "views": f"{1000 * i:,}",
                "duration": "10:30",
                "published_at": "2024-01-01"
            }
            for i in range(1, min(max_results + 1, 6))
        ]
        
        content = [
            types.TextContent(
                type="text",
                text=f"'{query}' 검색 결과 ({len(results)}개):\n\n" + 
                     "\n".join([
                         f"• {r['title']} (조회수: {r['views']})"
                         for r in results
                     ])
            )
        ]
        
        return types.CallToolResult(content=content)
    
    async def youtube_get_video_info(self, arguments: Dict[str, Any]) -> types.CallToolResult:
        """YouTube 비디오 상세 정보"""
        video_id = arguments.get("video_id", "")
        
        # 시뮬레이션 데이터
        video_info = {
            "title": f"샘플 비디오: {video_id}",
            "description": "이것은 샘플 비디오 설명입니다.",
            "channel": "샘플 채널",
            "views": "1,234,567",
            "likes": "12,345",
            "duration": "15:30",
            "published_at": "2024-01-15",
            "tags": ["태그1", "태그2", "태그3"]
        }
        
        content = [
            types.TextContent(
                type="text",
                text=f"비디오 정보:\n" +
                     f"제목: {video_info['title']}\n" +
                     f"채널: {video_info['channel']}\n" +
                     f"조회수: {video_info['views']}\n" +
                     f"좋아요: {video_info['likes']}\n" +
                     f"길이: {video_info['duration']}\n" +
                     f"업로드: {video_info['published_at']}\n" +
                     f"태그: {', '.join(video_info['tags'])}"
            )
        ]
        
        return types.CallToolResult(content=content)
    
    async def youtube_get_channel_info(self, arguments: Dict[str, Any]) -> types.CallToolResult:
        """YouTube 채널 정보"""
        channel_id = arguments.get("channel_id", "")
        
        # 시뮬레이션 데이터
        channel_info = {
            "name": f"샘플 채널: {channel_id}",
            "subscribers": "1,234,567",
            "videos": "456",
            "description": "이것은 샘플 채널 설명입니다.",
            "created_at": "2020-01-01"
        }
        
        content = [
            types.TextContent(
                type="text",
                text=f"채널 정보:\n" +
                     f"이름: {channel_info['name']}\n" +
                     f"구독자: {channel_info['subscribers']}\n" +
                     f"비디오 수: {channel_info['videos']}\n" +
                     f"설명: {channel_info['description']}\n" +
                     f"생성일: {channel_info['created_at']}"
            )
        ]
        
        return types.CallToolResult(content=content)
    
    async def youtube_get_comments(self, arguments: Dict[str, Any]) -> types.CallToolResult:
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
            types.TextContent(
                type="text",
                text=f"댓글 ({len(comments)}개):\n\n" +
                     "\n".join([
                         f"• {c['author']}: {c['text']} (좋아요: {c['likes']})"
                         for c in comments
                     ])
            )
        ]
        
        return types.CallToolResult(content=content)
    
    async def youtube_analyze_trending(self, arguments: Dict[str, Any]) -> types.CallToolResult:
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
            types.TextContent(
                type="text",
                text=f"{region} 지역 {category} 카테고리 트렌딩:\n\n" +
                     "\n".join([
                         f"• {v['title']} - {v['channel']} (조회수: {v['views']})"
                         for v in trending_videos
                     ])
            )
        ]
        
        return types.CallToolResult(content=content)

async def main():
    """메인 함수"""
    # YouTube MCP 서버 생성
    youtube_server = YouTubeMCPServer()
    
    # stdio 서버로 실행
    async with stdio_server() as (read_stream, write_stream):
        await youtube_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="youtube-mcp-server",
                server_version="1.0.0",
                capabilities=youtube_server.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
