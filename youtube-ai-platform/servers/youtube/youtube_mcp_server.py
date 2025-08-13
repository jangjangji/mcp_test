#!/usr/bin/env python3
"""
YouTube MCP 서버 - MCP 프로토콜로 직접 통신
HTTP 래퍼 없이 MCP 툴을 직접 실행
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel import NotificationOptions
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
    JSONRPCError
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeMCPServer:
    """YouTube 데이터 처리 MCP 서버"""
    
    def __init__(self):
        """MCP 서버 초기화"""
        self.server = Server("youtube-mcp-server")
        self._register_tools()
    
    def _register_tools(self):
        """MCP 도구들 등록"""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """사용 가능한 도구 목록 반환"""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="youtube_search",
                        description="YouTube에서 동영상을 검색합니다",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "검색할 키워드"
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "최대 결과 수 (기본값: 5)",
                                    "default": 5
                                }
                            },
                            "required": ["query"]
                        }
                    ),
                    Tool(
                        name="get_video_info",
                        description="YouTube 동영상의 상세 정보를 가져옵니다",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "video_id": {
                                    "type": "string",
                                    "description": "YouTube 동영상 ID"
                                }
                            },
                            "required": ["video_id"]
                        }
                    ),
                    Tool(
                        name="download_video",
                        description="YouTube 동영상을 다운로드합니다",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "video_id": {
                                    "type": "string",
                                    "description": "YouTube 동영상 ID"
                                },
                                "quality": {
                                    "type": "string",
                                    "description": "동영상 품질 (기본값: 'best')",
                                    "default": "best"
                                }
                            },
                            "required": ["video_id"]
                        }
                    )
                ]
            )
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """MCP 도구 호출 처리"""
            try:
                if name == "youtube_search":
                    return await self._youtube_search(arguments)
                elif name == "get_video_info":
                    return await self._get_video_info(arguments)
                elif name == "download_video":
                    return await self._download_video(arguments)
                else:
                    raise JSONRPCError(
                        code=-32600,  # Invalid Request
                        message=f"알 수 없는 도구: {name}"
                    )
            except Exception as e:
                logger.error(f"도구 실행 오류: {e}")
                raise JSONRPCError(
                    code=-32603,  # Internal Error
                    message=f"도구 실행 중 오류 발생: {str(e)}"
                )
    
    async def _youtube_search(self, arguments: Dict[str, Any]) -> CallToolResult:
        """YouTube 검색 시뮬레이션"""
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 5)
        
        logger.info(f"🔍 YouTube 검색: '{query}' (최대 {max_results}개)")
        
        # 시뮬레이션된 검색 결과
        results = [
            {
                "title": f"{query} 관련 동영상 1",
                "video_id": "abc123",
                "channel": "테스트 채널",
                "duration": "10:30",
                "views": "1,000",
                "thumbnail": "https://example.com/thumb1.jpg"
            },
            {
                "title": f"{query} 관련 동영상 2", 
                "video_id": "def456",
                "channel": "테스트 채널 2",
                "duration": "5:15",
                "views": "500",
                "thumbnail": "https://example.com/thumb2.jpg"
            }
        ][:max_results]
        
        logger.info(f"✅ 검색 완료: {len(results)}개 결과")
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"검색 결과: {len(results)}개\n" + 
                         "\n".join([f"{i+1}. {r['title']} ({r['duration']})" for i, r in enumerate(results)])
                )
            ]
        )
    
    async def _get_video_info(self, arguments: Dict[str, Any]) -> CallToolResult:
        """동영상 정보 가져오기 시뮬레이션"""
        video_id = arguments.get("video_id", "")
        
        logger.info(f"📹 동영상 정보 조회: {video_id}")
        
        # 시뮬레이션된 동영상 정보
        video_info = {
            "title": "테스트 동영상",
            "description": "이것은 테스트 동영상입니다.",
            "duration": "10:30",
            "views": "1,000",
            "likes": "100",
            "channel": "테스트 채널",
            "upload_date": "2024-01-01"
        }
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"동영상 정보:\n제목: {video_info['title']}\n채널: {video_info['channel']}\n길이: {video_info['duration']}"
                )
            ]
        )
    
    async def _download_video(self, arguments: Dict[str, Any]) -> CallToolResult:
        """동영상 다운로드 시뮬레이션"""
        video_id = arguments.get("video_id", "")
        quality = arguments.get("quality", "best")
        
        logger.info(f"⬇️ 동영상 다운로드: {video_id} (품질: {quality})")
        
        # 시뮬레이션된 다운로드
        download_info = {
            "status": "완료",
            "file_path": f"/downloads/{video_id}.mp4",
            "file_size": "50MB",
            "quality": quality
        }
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"다운로드 완료!\n파일: {download_info['file_path']}\n크기: {download_info['file_size']}\n품질: {download_info['quality']}"
                )
            ]
        )

async def main():
    """MCP 서버 메인 함수"""
    logger.info("🚀 YouTube MCP 서버 시작 중...")
    
    # YouTube MCP 서버 인스턴스 생성
    youtube_server = YouTubeMCPServer()
    
    # stdio_server를 사용하여 MCP 프로토콜로 통신
    async with stdio_server() as (read_stream, write_stream):
        logger.info("✅ YouTube MCP 서버가 stdio로 실행 중입니다.")
        
        # MCP 서버 실행
        await youtube_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="youtube-mcp-server",
                server_version="1.9.4",
                capabilities=youtube_server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
