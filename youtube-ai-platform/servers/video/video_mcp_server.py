#!/usr/bin/env python3
"""
Video MCP 서버 - 기존 VideoSearchSystem 활용

이 파일은 기존에 완벽하게 구현된 VideoSearchSystem을 MCP(Model Context Protocol) 도구로 변환한 서버입니다.
MCP는 AI 모델과 도구들을 연결하는 표준 프로토콜입니다.

주요 기능:
1. 비디오 검색: CLIP AI 모델로 텍스트로 비디오 장면을 검색
2. 비디오 추가: 새로운 비디오를 CLIP AI 모델로 분석하여 데이터베이스에 저장
3. 프레임 추출: 비디오에서 이미지 프레임을 추출
"""

# 필요한 Python 라이브러리들을 가져오기
import asyncio          # asyncio: 비동기 프로그래밍을 위한 라이브러리 (여러 작업을 동시에 처리)
import logging          # logging: 로그(기록) 출력을 위한 라이브러리
import os               # os: 운영체제 관련 기능 (파일 경로, 환경변수 등)
from typing import Any, Dict, List, Optional  # typing: 데이터 타입 힌트를 위한 라이브러리
# Any: 어떤 타입이든 가능, Dict: 딕셔너리(키-값 쌍), List: 리스트, Optional: 있을 수도 없을 수도 있음

# 기존에 완벽하게 구현된 VideoSearchSystem 가져오기
# 이 클래스는 CLIP AI 모델을 사용하여 비디오 검색을 수행하는 완성된 시스템입니다
from video_search_system import VideoSearchSystem

# MCP(Model Context Protocol) 서버 관련 라이브러리들
from mcp.server import Server                    # Server: MCP 서버 기본 클래스
from mcp.server.stdio import stdio_server        # stdio_server: 표준 입출력으로 MCP 통신
from mcp.server.models import InitializationOptions  # InitializationOptions: 서버 초기화 옵션
from mcp.server.lowlevel import NotificationOptions  # NotificationOptions: 알림 옵션
from mcp.types import (                          # MCP 타입들
    CallToolResult,                              # CallToolResult: 도구 호출 결과
    ListToolsResult,                             # ListToolsResult: 도구 목록 결과
    TextContent,                                 # TextContent: 텍스트 내용
    Tool,                                        # Tool: 도구 정의
    JSONRPCError                                 # JSONRPCError: JSON-RPC 오류
)

# HTTP 서버를 위한 추가 라이브러리들
from fastapi import FastAPI, HTTPException       # FastAPI: 현대적인 웹 프레임워크
from fastapi.middleware.cors import CORSMiddleware  # CORSMiddleware: 웹 브라우저 CORS 설정
from pydantic import BaseModel                   # BaseModel: 데이터 검증을 위한 모델
import uvicorn                                   # uvicorn: ASGI 서버 (FastAPI 실행용)

# 로깅(기록) 설정 - 프로그램 실행 중 일어나는 일들을 기록
logging.basicConfig(level=logging.INFO)          # 로그 레벨을 INFO로 설정 (중요한 정보만 출력)
logger = logging.getLogger(__name__)             # 현재 파일의 로거 생성

# FastAPI 웹 애플리케이션 생성
app = FastAPI(title="Video MCP HTTP Server", version="2.0.0")  # 제목과 버전 설정

# CORS(Cross-Origin Resource Sharing) 설정 - 웹 브라우저에서 다른 도메인 접근 허용
app.add_middleware(
    CORSMiddleware,                              # CORS 미들웨어 추가
    allow_origins=["*"],                         # 모든 도메인에서 접근 허용 (* = 모든 것)
    allow_credentials=True,                      # 쿠키, 인증 정보 등 허용
    allow_methods=["*"],                         # 모든 HTTP 메서드 허용 (GET, POST, PUT, DELETE 등)
    allow_headers=["*"],                         # 모든 HTTP 헤더 허용
)

# ===== HTTP API 요청/응답 모델 정의 =====

class VideoSearchRequest(BaseModel):
    """비디오 검색 요청 데이터 구조체"""
    query: str                                   # query: 검색할 텍스트 (예: "강아지가 헤엄치는 장면")
    top_k: Optional[int] = 5                    # top_k: 상위 몇 개 결과를 반환할지 (선택사항, 기본값 5)

class VideoAddRequest(BaseModel):
    """비디오 추가 요청 데이터 구조체"""
    video_path: str                              # video_path: 비디오 파일이 저장된 경로
    video_name: str                              # video_name: 비디오의 이름

class ExtractFramesRequest(BaseModel):
    """프레임 추출 요청 데이터 구조체"""
    video_path: str                              # video_path: 비디오 파일 경로
    fps: Optional[int] = 2                      # fps: 초당 몇 프레임을 추출할지 (선택사항, 기본값 2)

class MCPResponse(BaseModel):
    """MCP 도구 응답 데이터 구조체"""
    success: bool                                # success: 성공 여부 (True/False)
    data: Optional[Dict[str, Any]] = None       # data: 성공시 반환할 데이터 (선택사항)
    error: Optional[str] = None                 # error: 실패시 오류 메시지 (선택사항)

# ===== Video MCP 서버 클래스 정의 =====

class VideoMCPServer:
    """기존 VideoSearchSystem을 활용한 MCP 서버 클래스"""
    
    def __init__(self):
        """MCP 서버 초기화 (생성자)"""
        self.server = Server("video-mcp-server")  # "video-mcp-server"라는 이름으로 MCP 서버 생성
        
        # 기존에 완벽하게 구현된 VideoSearchSystem 사용
        logger.info("🚀 기존 VideoSearchSystem 로딩 중...")  # 로그 출력: VideoSearchSystem 로딩 시작
        try:                                 # try: 오류가 발생할 수 있는 코드 블록
            self.video_system = VideoSearchSystem()  # VideoSearchSystem 인스턴스 생성
            logger.info("✅ VideoSearchSystem 로드 완료!")  # 로그 출력: 로딩 성공
        except Exception as e:               # except: 오류가 발생했을 때 처리
            logger.error(f"❌ VideoSearchSystem 로드 실패: {e}")  # 로그 출력: 로딩 실패
            self.video_system = None         # video_system을 None으로 설정
        
        # 도구들을 등록하는 함수 호출
        self._register_tools()               # MCP 도구들을 등록하는 함수 호출
        
        logger.info("✅ Video MCP 서버 초기화 완료!")  # 로그 출력: 초기화 완료
    
    def _register_tools(self):
        """MCP 도구들을 등록하는 함수"""
        
        @self.server.list_tools()                # @self.server.list_tools(): 도구 목록을 반환하는 함수를 등록
        async def list_tools() -> ListToolsResult:
            """사용 가능한 도구 목록을 반환하는 함수"""
            return ListToolsResult(               # ListToolsResult: 도구 목록 결과 객체 반환
                tools=[                          # tools: 도구들의 리스트
                    Tool(                        # Tool: 첫 번째 도구 정의
                        name="video_search",      # name: 도구 이름
                        description="CLIP AI 모델을 사용하여 비디오 데이터베이스에서 유사한 장면을 검색합니다",  # description: 도구 설명
                        inputSchema={             # inputSchema: 입력 데이터의 형태 정의
                            "type": "object",    # type: 객체 형태
                            "properties": {      # properties: 속성들 정의
                                "query": {       # query 속성
                                    "type": "string",                    # type: 문자열
                                    "description": "검색할 텍스트 설명"   # description: 속성 설명
                                },
                                "top_k": {      # top_k 속성
                                    "type": "integer",                   # type: 정수
                                    "description": "반환할 최대 결과 수 (기본값: 5)",  # description: 속성 설명
                                    "default": 5                         # default: 기본값
                                }
                            },
                            "required": ["query"]  # required: 반드시 필요한 속성들
                        }
                    ),
                    Tool(                        # Tool: 두 번째 도구 정의
                        name="add_video",         # name: 도구 이름
                        description="새로운 비디오를 CLIP AI 모델로 분석하여 데이터베이스에 추가합니다",  # description: 도구 설명
                        inputSchema={             # inputSchema: 입력 데이터의 형태 정의
                            "type": "object",    # type: 객체 형태
                            "properties": {      # properties: 속성들 정의
                                "video_path": {  # video_path 속성
                                    "type": "string",                    # type: 문자열
                                    "description": "비디오 파일 경로"     # description: 속성 설명
                                },
                                "video_name": {  # video_name 속성
                                    "type": "string",                    # type: 문자열
                                    "description": "비디오 이름 (선택사항)"  # description: 속성 설명
                                }
                            },
                            "required": ["video_path"]  # required: 반드시 필요한 속성들 (video_name은 선택사항)
                        }
                    ),
                    Tool(                        # Tool: 세 번째 도구 정의
                        name="extract_frames",    # name: 도구 이름
                        description="비디오에서 프레임을 추출합니다",      # description: 도구 설명
                        inputSchema={             # inputSchema: 입력 데이터의 형태 정의
                            "type": "object",    # type: 객체 형태
                            "properties": {      # properties: 속성들 정의
                                "video_path": {  # video_path 속성
                                    "type": "string",                    # type: 문자열
                                    "description": "비디오 파일 경로"     # description: 속성 설명
                                },
                                "fps": {        # fps 속성
                                    "type": "integer",                   # type: 정수
                                    "description": "초당 프레임 수 (기본값: 2)",  # description: 속성 설명
                                    "default": 2                         # default: 기본값
                                }
                            },
                            "required": ["video_path"]  # required: 반드시 필요한 속성들
                        }
                    )
                ]
            )

        @self.server.call_tool()                 # @self.server.call_tool(): 도구를 호출하는 함수를 등록
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """MCP 도구를 호출하는 함수"""
            logger.info(f"🔧 도구 호출: {name}")  # 로그 출력: 어떤 도구가 호출되었는지 기록
            
            try:                                 # try: 오류가 발생할 수 있는 코드 블록
                if name == "video_search":       # 만약 도구 이름이 "video_search"라면
                    return await self._video_search(arguments)  # 비디오 검색 함수 호출
                elif name == "add_video":        # 만약 도구 이름이 "add_video"라면
                    return await self._add_video(arguments)     # 비디오 추가 함수 호출
                elif name == "extract_frames":   # 만약 도구 이름이 "extract_frames"라면
                    return await self._extract_frames(arguments) # 프레임 추출 함수 호출
                else:                            # 그 외의 도구 이름이라면
                    raise JSONRPCError(          # JSONRPCError 발생 (알 수 없는 도구)
                        code=-32601,             # code: 오류 코드 (-32601 = 메서드를 찾을 수 없음)
                        message=f"알 수 없는 도구: {name}"  # message: 오류 메시지
                    )
            except Exception as e:               # except: 오류가 발생했을 때 처리
                logger.error(f"도구 실행 오류: {e}")  # 로그 출력: 오류 내용 기록
                raise JSONRPCError(              # JSONRPCError 발생
                    code=-32603,                 # code: 오류 코드 (-32603 = 내부 오류)
                    message=f"도구 실행 중 오류 발생: {str(e)}"  # message: 오류 메시지
                )

    async def _video_search(self, arguments: Dict[str, Any]) -> CallToolResult:
        """기존 VideoSearchSystem을 사용한 비디오 검색"""
        query = arguments.get("query", "")       # query: 검색어 가져오기 (없으면 빈 문자열)
        top_k = arguments.get("top_k", 5)        # top_k: 상위 몇 개 결과를 반환할지 (없으면 5)
        
        logger.info(f"🔍 CLIP AI 비디오 검색: '{query}' (최대 {top_k}개)")  # 로그 출력: 검색 시작
        
        try:                                     # try: 오류가 발생할 수 있는 코드 블록
            if not self.video_system:            # 만약 VideoSearchSystem이 로드되지 않았다면
                raise Exception("VideoSearchSystem이 로드되지 않았습니다.")  # 예외 발생
            
            # 기존에 구현된 search_video_in_db 함수 사용
            # 이 함수는 CLIP AI 모델을 사용하여 실제 데이터베이스에서 검색을 수행합니다
            results = self.video_system.search_video_in_db(query, top_k)
            
            if not results:                      # 만약 검색 결과가 없다면
                return CallToolResult(           # CallToolResult: 도구 호출 결과 반환
                    content=[                    # content: 결과 내용 리스트
                        TextContent(             # TextContent: 텍스트 형태의 내용
                            type="text",         # type: 텍스트 타입
                            text=f"검색 결과가 없습니다: '{query}'"  # text: 결과 텍스트
                        )
                    ]
                )
            
            # 검색 결과를 텍스트로 변환
            result_text = f"CLIP AI 검색 결과: {len(results)}개\n"  # result_text: 결과 텍스트 (첫 줄)
            for i, result in enumerate(results): # 각 검색 결과를 하나씩 처리
                # 시간을 HH:MM:SS 형식으로 변환 (초 단위를 시간 형식으로)
                seconds = result["timestamp"]    # seconds: 초 단위 시간
                hours = int(seconds // 3600)     # hours: 시간 (3600초 = 1시간)
                minutes = int((seconds % 3600) // 60)  # minutes: 분 (60초 = 1분)
                secs = int(seconds % 60)         # secs: 초
                timestamp = f"{hours:02d}:{minutes:02d}:{secs:02d}"  # timestamp: HH:MM:SS 형식
                
                # 각 결과를 텍스트로 변환
                result_text += f"{i+1}. {result['video_id']} - {timestamp} (유사도: {result['similarity']:.3f})\n"  # 결과 정보
                result_text += f"   경로: {result['video_path']}\n"  # 비디오 경로 정보
            
            logger.info(f"✅ CLIP AI 검색 완료: {len(results)}개 결과")  # 로그 출력: 검색 완료
            
            return CallToolResult(               # CallToolResult: 도구 호출 결과 반환
                content=[                        # content: 결과 내용 리스트
                    TextContent(                 # TextContent: 텍스트 형태의 내용
                        type="text",             # type: 텍스트 타입
                        text=result_text         # text: 완성된 결과 텍스트
                    )
                ]
            )
            
        except Exception as e:                   # except: 오류가 발생했을 때 처리
            logger.error(f"CLIP AI 검색 실패: {e}")  # 로그 출력: 오류 내용 기록
            raise JSONRPCError(                  # JSONRPCError 발생
                code=-32603,                     # code: 오류 코드 (-32603 = 내부 오류)
                message=f"CLIP AI 검색 중 오류 발생: {str(e)}"  # message: 오류 메시지
            )
    
    async def _add_video(self, arguments: Dict[str, Any]) -> CallToolResult:
        """기존 VideoSearchSystem을 사용한 비디오 추가"""
        video_path = arguments.get("video_path", "")  # video_path: 비디오 파일 경로
        video_name = arguments.get("video_name", None)  # video_name: 비디오 이름 (선택사항)
        
        logger.info(f"📹 CLIP AI 비디오 분석 시작: {video_path}")  # 로그 출력: 비디오 분석 시작
        
        try:                                     # try: 오류가 발생할 수 있는 코드 블록
            if not self.video_system:            # 만약 VideoSearchSystem이 로드되지 않았다면
                raise Exception("VideoSearchSystem이 로드되지 않았습니다.")  # 예외 발생
            
            # 기존에 구현된 add_video_to_db 함수 사용
            # 이 함수는 CLIP AI 모델을 사용하여 비디오를 분석하고 데이터베이스에 저장합니다
            video_id = self.video_system.add_video_to_db(video_path, video_name)
            
            logger.info(f"✅ CLIP AI 비디오 분석 완료: {video_id}")  # 로그 출력: 분석 완료
            
            return CallToolResult(               # CallToolResult: 도구 호출 결과 반환
                content=[                        # content: 결과 내용 리스트
                    TextContent(                 # TextContent: 텍스트 형태의 내용
                        type="text",             # type: 텍스트 타입
                        text=f"CLIP AI 비디오 분석 완료!\n"  # text: 결과 텍스트
                             f"비디오 ID: {video_id}\n"     # 비디오 ID
                             f"경로: {video_path}\n"        # 비디오 경로
                             f"이제 텍스트로 검색할 수 있습니다!"  # 안내 메시지
                    )
                ]
            )
            
        except Exception as e:                   # except: 오류가 발생했을 때 처리
            logger.error(f"CLIP AI 비디오 분석 실패: {e}")  # 로그 출력: 오류 내용 기록
            raise JSONRPCError(                  # JSONRPCError 발생
                code=-32603,                     # code: 오류 코드 (-32603 = 내부 오류)
                message=f"CLIP AI 비디오 분석 중 오류 발생: {str(e)}"  # message: 오류 메시지
            )
    
    async def _extract_frames(self, arguments: Dict[str, Any]) -> CallToolResult:
        """기존 VideoSearchSystem을 사용한 프레임 추출"""
        video_path = arguments.get("video_path", "")  # video_path: 비디오 파일 경로
        fps = arguments.get("fps", 2)                # fps: 초당 프레임 수 (없으면 2)
        
        logger.info(f"🎬 프레임 추출: {video_path} (FPS: {fps})")  # 로그 출력: 프레임 추출 시작
        
        try:                                     # try: 오류가 발생할 수 있는 코드 블록
            if not self.video_system:            # 만약 VideoSearchSystem이 로드되지 않았다면
                raise Exception("VideoSearchSystem이 로드되지 않았습니다.")  # 예외 발생
            
            # 기존에 구현된 extract_frames 함수 사용
            # 이 함수는 비디오에서 프레임을 추출합니다
            frames = self.video_system.extract_frames(video_path, fps)
            
            logger.info(f"✅ 프레임 추출 완료: {len(frames)}개 프레임")  # 로그 출력: 프레임 추출 완료
            
            return CallToolResult(               # CallToolResult: 도구 호출 결과 반환
                content=[                        # content: 결과 내용 리스트
                    TextContent(                 # TextContent: 텍스트 형태의 내용
                        type="text",             # type: 텍스트 타입
                        text=f"프레임 추출 완료!\n"  # text: 결과 텍스트
                             f"비디오: {video_path}\n"        # 비디오 경로
                             f"추출된 프레임: {len(frames)}개\n"  # 추출된 프레임 수
                             f"FPS: {fps}"                    # 초당 프레임 수
                    )
                ]
            )
            
        except Exception as e:                   # except: 오류가 발생했을 때 처리
            logger.error(f"프레임 추출 실패: {e}")  # 로그 출력: 오류 내용 기록
            raise JSONRPCError(                  # JSONRPCError 발생
                code=-32603,                     # code: 오류 코드 (-32603 = 내부 오류)
                message=f"프레임 추출 중 오류 발생: {str(e)}"  # message: 오류 메시지
            )

# MCP 서버 인스턴스 생성 (클래스로부터 객체 생성)
mcp_server = VideoMCPServer()

# ===== HTTP API 엔드포인트들 정의 =====

@app.get("/")                                    # @app.get("/"): GET 요청을 "/" 경로로 받는 함수
async def root():
    """루트 엔드포인트 (메인 페이지)"""
    return {"message": "CLIP AI Video MCP HTTP Server", "status": "running"}  # JSON 응답 반환

@app.get("/tools")                               # @app.get("/tools"): GET 요청을 "/tools" 경로로 받는 함수
async def list_tools():
    """사용 가능한 MCP 도구 목록을 반환하는 엔드포인트"""
    tools = [                                    # tools: 도구 목록 리스트
        {                                        # 첫 번째 도구
            "name": "video_search",              # name: 도구 이름
            "description": "CLIP AI 모델을 사용하여 비디오 데이터베이스에서 유사한 장면을 검색합니다",  # description: 도구 설명
            "input_schema": {                    # input_schema: 입력 데이터 형태
                "type": "object",                # type: 객체 형태
                "properties": {                  # properties: 속성들
                    "query": {"type": "string", "description": "검색할 텍스트 설명"},  # query 속성
                    "top_k": {"type": "integer", "description": "반환할 최대 결과 수", "default": 5}  # top_k 속성
                },
                "required": ["query"]            # required: 반드시 필요한 속성들
            }
        },
        {                                        # 두 번째 도구
            "name": "add_video",                 # name: 도구 이름
            "description": "새로운 비디오를 CLIP AI 모델로 분석하여 데이터베이스에 추가합니다",  # description: 도구 설명
            "input_schema": {                    # input_schema: 입력 데이터 형태
                "type": "object",                # type: 객체 형태
                "properties": {                  # properties: 속성들
                    "video_path": {"type": "string", "description": "비디오 파일 경로"},  # video_path 속성
                    "video_name": {"type": "string", "description": "비디오 이름 (선택사항)"}  # video_name 속성
                },
                "required": ["video_path"]       # required: 반드시 필요한 속성들
            }
        },
        {                                        # 세 번째 도구
            "name": "extract_frames",            # name: 도구 이름
            "description": "비디오에서 프레임을 추출합니다",  # description: 도구 설명
            "input_schema": {                    # input_schema: 입력 데이터 형태
                "type": "object",                # type: 객체 형태
                "properties": {                  # properties: 속성들
                    "video_path": {"type": "string", "description": "비디오 파일 경로"},  # video_path 속성
                    "fps": {"type": "integer", "description": "초당 프레임 수", "default": 2}  # fps 속성
                },
                "required": ["video_path"]       # required: 반드시 필요한 속성들
            }
        }
    ]
    
    return {"tools": tools, "total": len(tools)}  # JSON 응답 반환: 도구 목록과 총 개수

@app.post("/tools/video_search")                # @app.post("/tools/video_search"): POST 요청을 "/tools/video_search" 경로로 받는 함수
async def video_search_tool(request: VideoSearchRequest):
    """CLIP AI 비디오 검색 MCP 도구를 HTTP로 호출하는 엔드포인트"""
    try:                                         # try: 오류가 발생할 수 있는 코드 블록
        # MCP 서버의 _video_search 함수 호출
        result = await mcp_server._video_search({
            "query": request.query,              # query: 요청에서 받은 검색어
            "top_k": request.top_k               # top_k: 요청에서 받은 상위 결과 수
        })
        return MCPResponse(success=True, data={"result": result.content[0].text})  # 성공 응답 반환
    except Exception as e:                       # except: 오류가 발생했을 때 처리
        logger.error(f"CLIP AI 비디오 검색 오류: {e}")   # 로그 출력: 오류 내용 기록
        return MCPResponse(success=False, error=str(e))  # 실패 응답 반환

@app.post("/tools/add_video")                   # @app.post("/tools/add_video"): POST 요청을 "/tools/add_video" 경로로 받는 함수
async def add_video_tool(request: VideoAddRequest):
    """CLIP AI 비디오 추가 MCP 도구를 HTTP로 호출하는 엔드포인트"""
    try:                                         # try: 오류가 발생할 수 있는 코드 블록
        # MCP 서버의 _add_video 함수 호출
        result = await mcp_server._add_video({
            "video_path": request.video_path,    # video_path: 요청에서 받은 비디오 경로
            "video_name": request.video_name     # video_name: 요청에서 받은 비디오 이름
        })
        return MCPResponse(success=True, data={"result": result.content[0].text})  # 성공 응답 반환
    except Exception as e:                       # except: 오류가 발생했을 때 처리
        logger.error(f"CLIP AI 비디오 추가 오류: {e}")   # 로그 출력: 오류 내용 기록
        return MCPResponse(success=False, error=str(e))  # 실패 응답 반환

@app.post("/tools/extract_frames")              # @app.post("/tools/extract_frames"): POST 요청을 "/tools/extract_frames" 경로로 받는 함수
async def extract_frames_tool(request: ExtractFramesRequest):
    """프레임 추출 MCP 도구를 HTTP로 호출하는 엔드포인트"""
    try:                                         # try: 오류가 발생할 수 있는 코드 블록
        # MCP 서버의 _extract_frames 함수 호출
        result = await mcp_server._extract_frames({
            "video_path": request.video_path,    # video_path: 요청에서 받은 비디오 경로
            "fps": request.fps                   # fps: 요청에서 받은 초당 프레임 수
        })
        return MCPResponse(success=True, data={"result": result.content[0].text})  # 성공 응답 반환
    except Exception as e:                       # except: 오류가 발생했을 때 처리
        logger.error(f"프레임 추출 오류: {e}")   # 로그 출력: 오류 내용 기록
        return MCPResponse(success=False, error=str(e))  # 실패 응답 반환

@app.get("/health")                              # @app.get("/health"): GET 요청을 "/health" 경로로 받는 함수
async def health_check():
    """헬스 체크 엔드포인트 (서버가 정상 작동하는지 확인)"""
    return {"status": "healthy", "service": "clip-ai-video-mcp-http-server"}  # JSON 응답 반환

# ===== MCP 서버 메인 함수 =====

async def main():
    """MCP 서버 메인 함수 (stdio 모드로 실행)"""
    logger.info("🚀 CLIP AI Video MCP 서버 시작 중...")  # 로그 출력: 서버 시작
    
    video_server = VideoMCPServer()             # VideoMCPServer 인스턴스 생성
    
    # stdio_server를 사용하여 MCP 프로토콜로 통신
    # stdio = Standard Input/Output (표준 입출력)
    # AI 모델과 직접 통신할 때 사용
    async with stdio_server() as (read_stream, write_stream):  # read_stream: 읽기 스트림, write_stream: 쓰기 스트림
        logger.info("✅ CLIP AI Video MCP 서버가 stdio로 실행 중입니다.")  # 로그 출력: stdio 모드 실행
        
        # MCP 서버 실행
        await video_server.server.run(           # await: 비동기 함수 완료 대기
            read_stream,                         # read_stream: AI 모델로부터 명령을 받는 스트림
            write_stream,                        # write_stream: AI 모델로 결과를 보내는 스트림
            InitializationOptions(               # InitializationOptions: 서버 초기화 옵션
                server_name="clip-ai-video-mcp-server",  # server_name: 서버 이름
                server_version="2.0.0",          # server_version: 서버 버전
                capabilities=video_server.server.get_capabilities(  # capabilities: 서버가 할 수 있는 일들
                    notification_options=NotificationOptions(),     # notification_options: 알림 옵션
                    experimental_capabilities={}                   # experimental_capabilities: 실험적 기능들
                )
            )
        )

# ===== 메인 실행 부분 =====

if __name__ == "__main__":                      # if __name__ == "__main__": 이 파일이 직접 실행될 때만 실행
    """메인 실행"""
    import sys                                   # sys: 시스템 관련 기능 (명령행 인수 등)
    
    # 명령행 인수로 실행 모드 결정
    if len(sys.argv) > 1 and sys.argv[1] == "--http":  # 만약 명령행에 "--http"가 있다면
        # HTTP 서버 모드로 실행
        logger.info("🚀 CLIP AI Video MCP HTTP 서버 시작 중...")  # 로그 출력: HTTP 서버 시작
        uvicorn.run(                             # uvicorn.run: ASGI 서버 실행
            app,                                 # app: FastAPI 애플리케이션
            host="0.0.0.0",                      # host: 모든 IP에서 접근 허용
            port=8002,                           # port: 8002 포트에서 서버 실행
            log_level="info"                     # log_level: 로그 레벨 설정
        )
    else:                                        # 그렇지 않다면 (명령행 인수가 없거나 "--http"가 아닌 경우)
        # 기본 stdio 모드로 실행 (AI 모델과 직접 통신)
        asyncio.run(main())                      # asyncio.run: 비동기 함수 실행
