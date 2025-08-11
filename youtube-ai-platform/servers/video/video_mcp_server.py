#!/usr/bin/env python3
"""
Video AI Platform - Video 전용 MCP 서버
비디오 처리 및 분석 기능을 제공하는 MCP 서버
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
app = FastAPI(title="Video MCP Server", version="1.0.0")

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

class VideoMCPServer:
    """비디오 처리 전용 MCP 서버"""
    
    def __init__(self):
        self.server = Server("video-mcp-server")
        self.setup_handlers()
        
    def setup_handlers(self):
        """MCP 서버 핸들러 설정"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """사용 가능한 도구 목록 반환"""
            tools = [
                Tool(
                    name="add_video_to_db",
                    description="비디오를 데이터베이스에 추가합니다",
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
                    name="search_video_in_db",
                    description="데이터베이스에서 비디오를 검색합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "검색할 키워드"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "반환할 결과 수",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="clear_video_from_db",
                    description="데이터베이스에서 비디오를 삭제합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_name": {
                                "type": "string",
                                "description": "삭제할 비디오 이름"
                            }
                        },
                        "required": ["video_name"]
                    }
                ),
                Tool(
                    name="save_single_video_embedding",
                    description="단일 비디오의 임베딩을 저장합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_url": {
                                "type": "string",
                                "description": "YouTube 비디오 URL"
                            }
                        },
                        "required": ["video_url"]
                    }
                ),
                Tool(
                    name="save_single_video_semantic_embedding",
                    description="단일 비디오의 시맨틱 임베딩을 저장합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_url": {
                                "type": "string",
                                "description": "YouTube 비디오 URL"
                            },
                            "chunk_method": {
                                "type": "string",
                                "description": "청킹 방법",
                                "default": "semantic"
                            }
                        },
                        "required": ["video_url"]
                    }
                ),
                Tool(
                    name="compare_chunking_methods",
                    description="다양한 청킹 방법을 비교합니다",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_url": {
                                "type": "string",
                                "description": "YouTube 비디오 URL"
                            }
                        },
                        "required": ["video_url"]
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """도구 호출 처리"""
            try:
                if name == "add_video_to_db":
                    return await self.add_video_to_db(arguments)
                elif name == "search_video_in_db":
                    return await self.search_video_in_db(arguments)
                elif name == "clear_video_from_db":
                    return await self.clear_video_from_db(arguments)
                elif name == "save_single_video_embedding":
                    return await self.save_single_video_embedding(arguments)
                elif name == "save_single_video_semantic_embedding":
                    return await self.save_single_video_semantic_embedding(arguments)
                elif name == "compare_chunking_methods":
                    return await self.compare_chunking_methods(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Tool call error: {str(e)}")
                raise ValueError(f"Tool execution failed: {str(e)}")
    
    async def add_video_to_db(self, arguments: Dict[str, Any]) -> CallToolResult:
        """비디오를 데이터베이스에 추가"""
        video_path = arguments.get("video_path", "")
        video_name = arguments.get("video_name", "")
        
        # 시뮬레이션 결과
        content = [
            {
                "type": "text",
                "text": f"✅ 비디오 '{video_name}'이(가) 데이터베이스에 추가되었습니다.\n경로: {video_path}"
            }
        ]
        
        return CallToolResult(content=content)
    
    async def search_video_in_db(self, arguments: Dict[str, Any]) -> CallToolResult:
        """데이터베이스에서 비디오 검색"""
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 5)
        
        # 시뮬레이션 검색 결과
        results = [
            {
                "video_name": f"비디오_{i}",
                "similarity": round(0.9 - (i * 0.1), 3),
                "timestamp": f"00:0{i}:00"
            }
            for i in range(1, min(top_k + 1, 6))
        ]
        
        content = [
            {
                "type": "text",
                "text": f"'{query}' 검색 결과 ({len(results)}개):\n\n" +
                       "\n".join([
                           f"• {r['video_name']} - {r['timestamp']} (유사도: {r['similarity']})"
                           for r in results
                       ])
            }
        ]
        
        return CallToolResult(content=content)
    
    async def clear_video_from_db(self, arguments: Dict[str, Any]) -> CallToolResult:
        """데이터베이스에서 비디오 삭제"""
        video_name = arguments.get("video_name", "")
        
        # 시뮬레이션 결과
        content = [
            {
                "type": "text",
                "text": f"✅ 비디오 '{video_name}'이(가) 데이터베이스에서 삭제되었습니다."
            }
        ]
        
        return CallToolResult(content=content)
    
    async def save_single_video_embedding(self, arguments: Dict[str, Any]) -> CallToolResult:
        """단일 비디오 임베딩 저장"""
        video_url = arguments.get("video_url", "")
        
        # 시뮬레이션 결과
        content = [
            {
                "type": "text",
                "text": f"✅ 비디오 임베딩이 저장되었습니다.\nURL: {video_url}"
            }
        ]
        
        return CallToolResult(content=content)
    
    async def save_single_video_semantic_embedding(self, arguments: Dict[str, Any]) -> CallToolResult:
        """단일 비디오 시맨틱 임베딩 저장"""
        video_url = arguments.get("video_url", "")
        chunk_method = arguments.get("chunk_method", "semantic")
        
        # 시뮬레이션 결과
        content = [
            {
                "type": "text",
                "text": f"✅ 비디오 시맨틱 임베딩이 저장되었습니다.\nURL: {video_url}\n청킹 방법: {chunk_method}"
            }
        ]
        
        return CallToolResult(content=content)
    
    async def compare_chunking_methods(self, arguments: Dict[str, Any]) -> CallToolResult:
        """청킹 방법 비교"""
        video_url = arguments.get("video_url", "")
        
        # 시뮬레이션 비교 결과
        content = [
            {
                "type": "text",
                "text": f"청킹 방법 비교 결과:\n\n" +
                       f"• Semantic 청킹: 가장 정확한 결과\n" +
                       f"• Fixed 청킹: 빠른 처리 속도\n" +
                       f"• Adaptive 청킹: 균형잡힌 성능\n\n" +
                       f"비디오 URL: {video_url}"
            }
        ]
        
        return CallToolResult(content=content)

# Video MCP 서버 인스턴스 생성
video_server = VideoMCPServer()

# HTTP 엔드포인트들
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "Video MCP Server", "status": "running"}

@app.get("/tools")
async def list_tools():
    """사용 가능한 도구 목록 반환"""
    try:
        # MCP 서버 대신 직접 tool 목록 반환
        tools = [
            {
                "name": "add_video_to_db",
                "description": "비디오를 데이터베이스에 추가합니다"
            },
            {
                "name": "search_video_in_db",
                "description": "데이터베이스에서 비디오를 검색합니다"
            },
            {
                "name": "clear_video_from_db",
                "description": "데이터베이스에서 비디오를 삭제합니다"
            },
            {
                "name": "save_single_video_embedding",
                "description": "단일 비디오의 임베딩을 저장합니다"
            },
            {
                "name": "save_single_video_semantic_embedding",
                "description": "단일 비디오의 시맨틱 임베딩을 저장합니다"
            },
            {
                "name": "compare_chunking_methods",
                "description": "다양한 청킹 방법을 비교합니다"
            }
        ]
        return {"tools": tools}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add_video_to_db")
async def add_video_to_db_endpoint(request: Dict[str, Any]):
    """비디오 추가 엔드포인트"""
    try:
        # MCP 서버 대신 직접 함수 호출
        result = await video_server.add_video_to_db(request)
        return {"result": result.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search_video_in_db")
async def search_video_in_db_endpoint(request: Dict[str, Any]):
    """비디오 검색 엔드포인트"""
    try:
        # MCP 서버 대신 직접 함수 호출
        result = await video_server.search_video_in_db(request)
        return {"result": result.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clear_video_from_db")
async def clear_video_from_db_endpoint(request: Dict[str, Any]):
    """비디오 삭제 엔드포인트"""
    try:
        # MCP 서버 대신 직접 함수 호출
        result = await video_server.clear_video_from_db(request)
        return {"result": result.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_single_video_embedding")
async def save_single_video_embedding_endpoint(request: Dict[str, Any]):
    """비디오 임베딩 저장 엔드포인트"""
    try:
        # MCP 서버 대신 직접 함수 호출
        result = await video_server.save_single_video_embedding(request)
        return {"result": result.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_single_video_semantic_embedding")
async def save_single_video_semantic_embedding_endpoint(request: Dict[str, Any]):
    """비디오 시맨틱 임베딩 저장 엔드포인트"""
    try:
        # MCP 서버 대신 직접 함수 호출
        result = await video_server.save_single_video_semantic_embedding(request)
        return {"result": result.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare_chunking_methods")
async def compare_chunking_methods_endpoint(request: Dict[str, Any]):
    """청킹 방법 비교 엔드포인트"""
    try:
        # MCP 서버 대신 직접 함수 호출
        result = await video_server.compare_chunking_methods(request)
        return {"result": result.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    """메인 함수"""
    logger.info("🚀 Video MCP HTTP 서버 시작 중...")
    
    # HTTP 서버 실행
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
