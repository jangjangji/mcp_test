use axum::{
    extract::Json,
    http::Method,
    response::{Json as JsonResponse, Html},
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::process::{Command, Stdio, Child};
use std::io::{Read, Write, BufRead, BufReader};
use std::sync::{Arc, Mutex};
use tokio::sync::mpsc;

// MCP 프로토콜 구조체들
#[derive(Debug, Serialize, Deserialize)]
struct MCPRequest {
    jsonrpc: String,
    id: String,
    method: String,
    params: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
struct MCPResponse {
    jsonrpc: String,
    id: String,
    result: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
struct MCPError {
    jsonrpc: String,
    id: String,
    error: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
struct MCPTool {
    name: String,
    description: String,
    inputSchema: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
struct MCPToolCallResult {
    content: Vec<serde_json::Value>,
}

// MCP 클라이언트 구조체
struct MCPClient {
    youtube_process: Option<Child>,
    video_process: Option<Child>,
}

impl MCPClient {
    fn new() -> Self {
        Self {
            youtube_process: None,
            video_process: None,
        }
    }

    // MCP 서버들과 연결 (직접 프로세스 생성)
    async fn connect_to_mcp_servers(&mut self) -> Result<(), anyhow::Error> {
        // YouTube MCP 서버 프로세스 생성
        let youtube_process = Command::new("python")
            .arg("youtube_mcp_server.py")
            .current_dir("/app/youtube")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()?;
        
        self.youtube_process = Some(youtube_process);

        // Video MCP 서버 프로세스 생성
        let video_process = Command::new("python")
            .arg("video_mcp_server.py")
            .current_dir("/app/video")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()?;
        
        self.video_process = Some(video_process);

        Ok(())
    }

    // YouTube MCP 서버와 통신
    async fn call_youtube_function(&mut self, function_name: &str, args: serde_json::Value) -> Result<String, anyhow::Error> {
        let request = MCPRequest {
            jsonrpc: "2.0".to_string(),
            id: "1".to_string(),
            method: "tools/call".to_string(),
            params: serde_json::json!({
                "name": function_name,
                "arguments": args
            }),
        };

        let response = self.send_mcp_request(&request, "youtube").await?;
        Ok(response)
    }

    // Video MCP 서버와 통신
    async fn call_video_function(&mut self, function_name: &str, args: serde_json::Value) -> Result<String, anyhow::Error> {
        let request = MCPRequest {
            jsonrpc: "2.0".to_string(),
            id: "1".to_string(),
            method: "tools/call".to_string(),
            params: serde_json::json!({
                "name": function_name,
                "arguments": args
            }),
        };

        let response = self.send_mcp_request(&request, "video").await?;
        Ok(response)
    }

    // MCP 요청 전송
    async fn send_mcp_request(&mut self, request: &MCPRequest, server_type: &str) -> Result<String, anyhow::Error> {
        let request_json = serde_json::to_string(request)?;
        
        let process = match server_type {
            "youtube" => &mut self.youtube_process,
            "video" => &mut self.video_process,
            _ => return Err(anyhow::anyhow!("알 수 없는 서버 타입: {}", server_type)),
        };

        if let Some(ref mut proc) = process {
            if let Some(stdin) = &mut proc.stdin {
                stdin.write_all(request_json.as_bytes())?;
                stdin.flush()?;
            }
            
            if let Some(stdout) = &mut proc.stdout {
                let mut buffer = Vec::new();
                stdout.read_to_end(&mut buffer)?;
                let response = String::from_utf8(buffer)?;
                return Ok(response);
            }
        }

        Err(anyhow::anyhow!("MCP 서버와 통신할 수 없습니다"))
    }

    // MCP 서버 초기화
    async fn initialize_mcp_server(&mut self, server_type: &str) -> Result<(), anyhow::Error> {
        let init_request = MCPRequest {
            jsonrpc: "2.0".to_string(),
            id: "1".to_string(),
            method: "initialize".to_string(),
            params: serde_json::json!({
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "rust-mcp-client",
                    "version": "1.0.0"
                }
            }),
        };

        let _response = self.send_mcp_request(&init_request, server_type).await?;
        Ok(())
    }
}

// 요청/응답 구조체들
#[derive(Debug, Deserialize)]
struct YouTubeSearchRequest {
    query: String,
    max_results: Option<i32>,
}

#[derive(Debug, Serialize)]
struct YouTubeSearchResponse {
    success: bool,
    data: Option<serde_json::Value>,
    error: Option<String>,
}

#[derive(Debug, Deserialize)]
struct VideoSearchRequest {
    query: String,
    top_k: Option<i32>,
}

#[derive(Debug, Serialize)]
struct VideoSearchResponse {
    success: bool,
    data: Option<serde_json::Value>,
    error: Option<String>,
}

#[tokio::main]
async fn main() {
    println!("🚀 YouTube Search API Server 시작 중...");
    println!("📍 서버 주소: http://0.0.0.0:8080");
    println!("🔧 MCP 서버와 연동 중...");

    // MCP 클라이언트 생성 및 서버 연결
    let mut mcp_client = MCPClient::new();
    if let Err(e) = mcp_client.connect_to_mcp_servers().await {
        eprintln!("MCP 서버 연결 실패: {}", e);
        return;
    }

    // MCP 서버들 초기화
    if let Err(e) = mcp_client.initialize_mcp_server("youtube").await {
        eprintln!("YouTube MCP 서버 초기화 실패: {}", e);
    }
    if let Err(e) = mcp_client.initialize_mcp_server("video").await {
        eprintln!("Video MCP 서버 초기화 실패: {}", e);
    }

    println!("✅ MCP 서버 연결 완료!");

    // CORS 미들웨어 설정
    let cors = tower_http::cors::CorsLayer::new()
        .allow_methods([Method::GET, Method::POST])
        .allow_origin(tower_http::cors::Any);

    // 라우터 설정
    let app = Router::new()
        .route("/", get(|| async { Html(include_str!("../static/index.html")) }))
        .route("/static/app.js", get(|| async { 
            let js_content = include_str!("../static/app.js");
            Html(js_content)
        }))
        .route("/api/youtube/search", post(youtube_search))
        .route("/api/search-video", post(video_search))
        .layer(cors);

    // 서버 시작
    let listener = tokio::net::TcpListener::bind("0.0.0.0:8080").await.unwrap();
    println!("✅ 서버가 시작되었습니다!");
    
    axum::serve(listener, app).await.unwrap();
}

// YouTube 검색 엔드포인트
async fn youtube_search(
    Json(payload): Json<YouTubeSearchRequest>,
) -> JsonResponse<YouTubeSearchResponse> {
    let mut mcp_client = MCPClient::new();
    
    let args = serde_json::json!({
        "query": payload.query,
        "max_results": payload.max_results.unwrap_or(5)
    });

    match mcp_client.call_youtube_function("youtube_search", args).await {
        Ok(response) => {
            JsonResponse(YouTubeSearchResponse {
                success: true,
                data: Some(serde_json::from_str(&response).unwrap_or_default()),
                error: None,
            })
        }
        Err(e) => {
            JsonResponse(YouTubeSearchResponse {
                success: false,
                data: None,
                error: Some(format!("MCP 함수 호출 오류: {}", e)),
            })
        }
    }
}

// 비디오 검색 엔드포인트
async fn video_search(
    Json(payload): Json<VideoSearchRequest>,
) -> JsonResponse<VideoSearchResponse> {
    let mut mcp_client = MCPClient::new();
    
    let args = serde_json::json!({
        "query": payload.query,
        "top_k": payload.top_k.unwrap_or(5)
    });

    match mcp_client.call_video_function("video_search", args).await {
        Ok(response) => {
            JsonResponse(VideoSearchResponse {
                success: true,
                data: Some(serde_json::from_str(&response).unwrap_or_default()),
                error: None,
            })
        }
        Err(e) => {
            JsonResponse(VideoSearchResponse {
                success: false,
                data: None,
                error: Some(format!("MCP 함수 호출 오류: {}", e)),
            })
        }
    }
} 