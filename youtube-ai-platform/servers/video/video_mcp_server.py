#!/usr/bin/env python3
"""
Video MCP 서버 - MCP 프로토콜로 직접 통신 및 HTTP API 제공
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

# HTTP 서버를 위한 추가 import
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="Video MCP HTTP Server", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청/응답 모델
class VideoSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class VideoAddRequest(BaseModel):
    video_path: str
    video_name: str

class ExtractFramesRequest(BaseModel):
    video_path: str
    fps: Optional[int] = 2

class MCPResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

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
            """MCP 도구 호출"""
            logger.info(f"🔧 도구 호출: {name}")
            
            try:
                if name == "video_search":
                    return await self._video_search(arguments)
                elif name == "add_video":
                    return await self._add_video(arguments)
                elif name == "extract_frames":
                    return await self._extract_frames(arguments)
                else:
                    raise JSONRPCError(
                        code=-32601,
                        message=f"알 수 없는 도구: {name}"
                    )
            except Exception as e:
                logger.error(f"도구 실행 오류: {e}")
                raise JSONRPCError(
                    code=-32603,
                    message=f"도구 실행 중 오류 발생: {str(e)}"
                )

    async def _video_search(self, arguments: Dict[str, Any]) -> CallToolResult:
        """비디오 검색 시뮬레이션"""
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 5)
        
        logger.info(f"🔍 비디오 검색: '{query}' (최대 {top_k}개)")
        
        # 시뮬레이션된 검색 결과
        results = [
            {
                "video_name": "dog_video",
                "timestamp": "00:00:05",
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

# MCP 서버 인스턴스 생성
mcp_server = VideoMCPServer()

# HTTP API 엔드포인트들
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "Video MCP HTTP Server", "status": "running"}

@app.get("/tools")
async def list_tools():
    """사용 가능한 MCP 도구 목록 반환"""
    tools = [
        {
            "name": "video_search",
            "description": "비디오 데이터베이스에서 유사한 장면을 검색합니다",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색할 텍스트 설명"},
                    "top_k": {"type": "integer", "description": "반환할 최대 결과 수", "default": 5}
                },
                "required": ["query"]
            }
        },
        {
            "name": "add_video",
            "description": "새로운 비디오를 데이터베이스에 추가합니다",
            "input_schema": {
                "type": "object",
                "properties": {
                    "video_path": {"type": "string", "description": "비디오 파일 경로"},
                    "video_name": {"type": "string", "description": "비디오 이름"}
                },
                "required": ["video_path", "video_name"]
            }
        },
        {
            "name": "extract_frames",
            "description": "비디오에서 프레임을 추출합니다",
            "input_schema": {
                "type": "object",
                "properties": {
                    "video_path": {"type": "string", "description": "비디오 파일 경로"},
                    "fps": {"type": "integer", "description": "초당 프레임 수", "default": 2}
                },
                "required": ["video_path"]
            }
        }
    ]
    
    return {"tools": tools, "total": len(tools)}

@app.post("/tools/video_search")
async def video_search_tool(request: VideoSearchRequest):
    """비디오 검색 MCP 도구"""
    try:
        result = await mcp_server._video_search({
            "query": request.query,
            "top_k": request.top_k
        })
        return MCPResponse(success=True, data={"result": result.content[0].text})
    except Exception as e:
        logger.error(f"비디오 검색 오류: {e}")
        return MCPResponse(success=False, error=str(e))

@app.post("/tools/add_video")
async def add_video_tool(request: VideoAddRequest):
    """비디오 추가 MCP 도구"""
    try:
        result = await mcp_server._add_video({
            "video_path": request.video_path,
            "video_name": request.video_name
        })
        return MCPResponse(success=True, data={"result": result.content[0].text})
    except Exception as e:
        logger.error(f"비디오 추가 오류: {e}")
        return MCPResponse(success=False, error=str(e))

@app.post("/tools/extract_frames")
async def extract_frames_tool(request: ExtractFramesRequest):
    """프레임 추출 MCP 도구"""
    try:
        result = await mcp_server._extract_frames({
            "video_path": request.video_path,
            "fps": request.fps
        })
        return MCPResponse(success=True, data={"result": result.content[0].text})
    except Exception as e:
        logger.error(f"프레임 추출 오류: {e}")
        return MCPResponse(success=False, error=str(e))

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "service": "video-mcp-http-server"}

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
    """메인 실행"""
    import sys
    
    # 명령행 인수로 실행 모드 결정
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        # HTTP 서버 모드로 실행
        logger.info("🚀 Video MCP HTTP 서버 시작 중...")
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8002, 
            log_level="info"
        )
    else:
        # 기본 stdio 모드로 실행
        asyncio.run(main())
