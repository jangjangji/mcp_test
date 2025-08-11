#!/usr/bin/env python3
"""
YouTube AI Platform - 비디오 처리 전용 MCP 서버
비디오 분석, 검색, 처리 기능을 제공하는 MCP 서버
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

class VideoMCPServer:
    """비디오 처리 전용 MCP 서버"""
    
    def __init__(self):
        self.server = Server("video-mcp-server")
        self.setup_handlers()
        
    def setup_handlers(self):
        """MCP 서버 핸들러 설정"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> types.ListToolsResult:
            """사용 가능한 도구 목록 반환"""
            tools = [
                types.Tool(
                    name="video_search",
                    description="비디오에서 텍스트로 검색합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "검색할 텍스트"
                            },
                            "video_id": {
                                "type": "string",
                                "description": "검색할 비디오 ID"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "반환할 최대 결과 수",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="video_add_to_db",
                    description="비디오를 데이터베이스에 추가합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_path": {
                                "type": "string",
                                "description": "비디오 파일 경로"
                            },
                            "video_id": {
                                "type": "string",
                                "description": "비디오 식별자"
                            }
                        },
                        "required": ["video_path"]
                    }
                ),
                types.Tool(
                    name="video_get_info",
                    description="비디오 정보를 가져옵니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_id": {
                                "type": "string",
                                "description": "비디오 ID"
                            }
                        },
                        "required": ["video_id"]
                    }
                ),
                types.Tool(
                    name="video_extract_frames",
                    description="비디오에서 프레임을 추출합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_path": {
                                "type": "string",
                                "description": "비디오 파일 경로"
                            },
                            "fps": {
                                "type": "integer",
                                "description": "초당 프레임 수",
                                "default": 2
                            }
                        },
                        "required": ["video_path"]
                    }
                ),
                types.Tool(
                    name="video_analyze_content",
                    description="비디오 내용을 분석합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_id": {
                                "type": "string",
                                "description": "비디오 ID"
                            }
                        },
                        "required": ["video_id"]
                    }
                ),
                types.Tool(
                    name="video_clear_db",
                    description="데이터베이스에서 비디오를 삭제합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_id": {
                                "type": "string",
                                "description": "삭제할 비디오 ID"
                            }
                        },
                        "required": ["video_id"]
                    }
                )
            ]
            return types.ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> types.CallToolResult:
            """도구 호출 처리"""
            try:
                if name == "video_search":
                    return await self.video_search(arguments)
                elif name == "video_add_to_db":
                    return await self.video_add_to_db(arguments)
                elif name == "video_get_info":
                    return await self.video_get_info(arguments)
                elif name == "video_extract_frames":
                    return await self.video_extract_frames(arguments)
                elif name == "video_analyze_content":
                    return await self.video_analyze_content(arguments)
                elif name == "video_clear_db":
                    return await self.video_clear_db(arguments)
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
    
    async def video_search(self, arguments: Dict[str, Any]) -> types.CallToolResult:
        """비디오에서 텍스트로 검색"""
        query = arguments.get("query", "")
        video_id = arguments.get("video_id", None)
        top_k = arguments.get("top_k", 5)
        
        # 시뮬레이션 검색 결과
        results = [
            {
                "video_id": video_id or "sample_video",
                "timestamp": 10.5 + i * 2.0,
                "similarity": 0.9 - i * 0.1
            }
            for i in range(min(top_k, 3))
        ]
        
        content = [
            types.TextContent(
                type="text",
                text=f"'{query}' 검색 결과 ({len(results)}개):\n\n" +
                     "\n".join([
                         f"• {r['video_id']} - {self.format_timestamp(r['timestamp'])} (유사도: {r['similarity']:.3f})"
                         for r in results
                     ])
            )
        ]
        
        return types.CallToolResult(content=content)
    
    async def video_add_to_db(self, arguments: Dict[str, Any]) -> types.CallToolResult:
        """비디오를 데이터베이스에 추가"""
        video_path = arguments.get("video_path", "")
        video_id = arguments.get("video_id", None)
        
        if video_id is None:
            video_id = os.path.basename(video_path)
        
        content = [
            types.TextContent(
                type="text",
                text=f"✅ 비디오 '{video_id}' DB 저장 완료 (시뮬레이션)"
            )
        ]
        
        return types.CallToolResult(content=content)
    
    def format_timestamp(self, seconds: float) -> str:
        """초를 HH:MM:SS 형식으로 변환"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    async def video_get_info(self, arguments: Dict[str, Any]) -> types.CallToolResult:
        """비디오 정보 가져오기"""
        video_id = arguments.get("video_id", "")
        
        content = [
            types.TextContent(
                type="text",
                text=f"비디오 정보:\n" +
                     f"ID: {video_id}\n" +
                     f"상태: 시뮬레이션 모드\n" +
                     f"분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        ]
        
        return types.CallToolResult(content=content)
    
    async def video_extract_frames(self, arguments: Dict[str, Any]) -> types.CallToolResult:
        """비디오에서 프레임 추출"""
        video_path = arguments.get("video_path", "")
        fps = arguments.get("fps", 2)
        
        content = [
            types.TextContent(
                type="text",
                text=f"프레임 추출 완료:\n" +
                     f"파일: {video_path}\n" +
                     f"초당 프레임: {fps}\n" +
                     f"상태: 시뮬레이션 모드"
            )
        ]
        
        return types.CallToolResult(content=content)
    
    async def video_analyze_content(self, arguments: Dict[str, Any]) -> types.CallToolResult:
        """비디오 내용 분석"""
        video_id = arguments.get("video_id", "")
        
        content = [
            types.TextContent(
                type="text",
                text=f"비디오 내용 분석:\n" +
                     f"ID: {video_id}\n" +
                     f"상태: 시뮬레이션 모드\n" +
                     f"분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        ]
        
        return types.CallToolResult(content=content)
    
    async def video_clear_db(self, arguments: Dict[str, Any]) -> types.CallToolResult:
        """데이터베이스에서 비디오 삭제"""
        video_id = arguments.get("video_id", "")
        
        content = [
            types.TextContent(
                type="text",
                text=f"✅ 비디오 '{video_id}' 데이터 삭제 완료 (시뮬레이션)"
            )
        ]
        
        return types.CallToolResult(content=content)

async def main():
    """메인 함수"""
    # 비디오 MCP 서버 생성
    video_server = VideoMCPServer()
    
    # stdio 서버로 실행
    async with stdio_server() as (read_stream, write_stream):
        await video_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="video-mcp-server",
                server_version="1.0.0",
                capabilities=video_server.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
