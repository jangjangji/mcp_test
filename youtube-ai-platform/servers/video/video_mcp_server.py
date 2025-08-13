#!/usr/bin/env python3
"""
Video MCP 서버 - MCP 프로토콜로 직접 통신
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

class VideoMCPServer:
    """비디오 처리 MCP 서버"""
    
    def __init__(self):
        """MCP 서버 초기화"""
        self.server = Server("video-mcp-server")
        self._register_tools()
    
    def _register_tools(self):
        """MCP 도구들 등록"""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """사용 가능한 도구 목록 반환"""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="video_search",
                        description="비디오 데이터베이스에서 유사한 장면을 검색합니다",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "검색할 텍스트 설명"
                                },
                                "top_k": {
                                    "type": "integer",
                                    "description": "반환할 최대 결과 수 (기본값: 5)",
                                    "default": 5
                                }
                            },
                            "required": ["query"]
                        }
                    ),
                    Tool(
                        name="add_video",
                        description="새로운 비디오를 데이터베이스에 추가합니다",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "video_path": {
                                    "type": "string",
                                    "description": "비디오 파일 경로"
                                },
                                "video_name": {
                                    "type": "string",
                                    "description": "비디오 이름"
                                }
                            },
                            "required": ["video_path", "video_name"]
                        }
                    ),
                    Tool(
                        name="extract_frames",
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
                                    "description": "초당 프레임 수 (기본값: 2)",
                                    "default": 2
                                }
                            },
                            "required": ["video_path"]
                        }
                    )
                ]
            )
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """MCP 도구 호출 처리"""
            try:
                if name == "video_search":
                    return await self._video_search(arguments)
                elif name == "add_video":
                    return await self._add_video(arguments)
                elif name == "extract_frames":
                    return await self._extract_frames(arguments)
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
    
    async def _video_search(self, arguments: Dict[str, Any]) -> CallToolResult:
        """비디오 검색 시뮬레이션"""
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 5)
        
        logger.info(f"🔍 비디오 검색: '{query}' (상위 {top_k}개)")
        
        # 시뮬레이션된 검색 결과
        results = [
            {
                "video_name": "dog_video",
                "timestamp": "00:00:09",
                "similarity": 1.000,
                "description": "강아지가 물에서 놀고 있는 장면"
            },
            {
                "video_name": "dog_video", 
                "timestamp": "00:00:12",
                "similarity": 0.996,
                "description": "강아지가 물에서 공을 무는 장면"
            },
            {
                "video_name": "dog_video",
                "timestamp": "00:00:07", 
                "similarity": 0.928,
                "description": "강아지가 물속에서 헤엄치는 장면"
            }
        ][:top_k]
        
        logger.info(f"✅ 검색 완료: {len(results)}개 결과")
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"검색 결과: {len(results)}개\n" + 
                         "\n".join([f"{i+1}. {r['video_name']} - {r['timestamp']} (유사도: {r['similarity']:.3f})" for i, r in enumerate(results)])
                )
            ]
        )
    
    async def _add_video(self, arguments: Dict[str, Any]) -> CallToolResult:
        """비디오 추가 시뮬레이션"""
        video_path = arguments.get("video_path", "")
        video_name = arguments.get("video_name", "")
        
        logger.info(f"📹 비디오 추가: {video_name} ({video_path})")
        
        # 시뮬레이션된 추가 과정
        add_info = {
            "status": "완료",
            "video_name": video_name,
            "frames_extracted": 15,
            "embeddings_created": 15,
            "database_updated": True
        }
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"비디오 추가 완료!\n이름: {add_info['video_name']}\n추출된 프레임: {add_info['frames_extracted']}개\n임베딩 생성: {add_info['embeddings_created']}개"
                )
            ]
        )
    
    async def _extract_frames(self, arguments: Dict[str, Any]) -> CallToolResult:
        """프레임 추출 시뮬레이션"""
        video_path = arguments.get("video_path", "")
        fps = arguments.get("fps", 2)
        
        logger.info(f"🎬 프레임 추출: {video_path} (FPS: {fps})")
        
        # 시뮬레이션된 프레임 추출
        frame_info = {
            "total_frames": 30,
            "extracted_frames": 15,
            "fps": fps,
            "output_directory": "/app/frames"
        }
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"프레임 추출 완료!\n총 프레임: {frame_info['total_frames']}개\n추출된 프레임: {frame_info['extracted_frames']}개\nFPS: {frame_info['fps']}"
                )
            ]
        )

async def main():
    """MCP 서버 메인 함수"""
    logger.info("🚀 Video MCP 서버 시작 중...")
    
    # Video MCP 서버 인스턴스 생성
    video_server = VideoMCPServer()
    
    # stdio_server를 사용하여 MCP 프로토콜로 통신
    async with stdio_server() as (read_stream, write_stream):
        logger.info("✅ Video MCP 서버가 stdio로 실행 중입니다.")
        
        # MCP 서버 실행
        await video_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="video-mcp-server",
                server_version="1.9.4",
                capabilities=video_server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
