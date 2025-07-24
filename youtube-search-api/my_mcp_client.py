#!/usr/bin/env python3
"""
MCP Client for Rust Backend
Rust 서버에서 Python MCP 함수들을 호출하기 위한 클라이언트
"""

import sys
import json
import os
import traceback

def call_mcp_function(function_name, args):
    """MCP 함수를 호출하는 함수"""
    try:
        # 현재 스크립트의 디렉토리에서 상위 디렉토리로 이동
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.join(current_dir, '..')
        os.chdir(parent_dir)
        
        # Python 경로에 현재 디렉토리 추가
        sys.path.insert(0, os.getcwd())
        
        # mcp_server.py를 직접 import
        import importlib.util
        spec = importlib.util.spec_from_file_location("mcp_server", "mcp_server.py")
        mcp_server = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mcp_server)
        
        # 함수 호출
        if function_name == "search_similar_youtube_video":
            result = mcp_server.search_similar_youtube_video(args.get("query", ""))
        elif function_name == "search_youtube_videos":
            result = mcp_server.search_youtube_videos(args.get("query", ""))
        elif function_name == "get_channel_info":
            result = mcp_server.get_channel_info(args.get("video_url", ""))
        elif function_name == "save_channel_youtube_embeddings":
            result = mcp_server.save_channel_youtube_embeddings(args.get("channel_id", ""))
        elif function_name == "get_youtube_transcript":
            result = mcp_server.get_youtube_transcript(args.get("url", ""))
        else:
            raise ValueError(f"Unknown function: {function_name}")
        
        # 결과가 이미 dict인 경우 JSON으로 변환
        if isinstance(result, dict):
            return result
        elif isinstance(result, list):
            # 리스트인 경우 그대로 반환
            return result
        else:
            # 문자열이나 다른 타입인 경우 dict로 감싸기
            return {"result": str(result)}
        
    except Exception as e:
        error_info = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "function_name": function_name,
            "args": args
        }
        return error_info

if __name__ == "__main__":
    if len(sys.argv) != 3:
        error_response = {"error": "Usage: python my_mcp_client.py <function_name> <args_json>"}
        print(json.dumps(error_response, ensure_ascii=False))
        sys.exit(1)
    
    function_name = sys.argv[1]
    args_json = sys.argv[2]
    
    try:
        args = json.loads(args_json)
        result = call_mcp_function(function_name, args)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        error_response = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "function_name": function_name,
            "args_json": args_json
        }
        print(json.dumps(error_response, ensure_ascii=False)) 