use axum::{
    extract::State,
    extract::Json,
    http::Method,
    response::{Html, Json as JsonResponse},
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::process::{Command, Stdio, Child};
use std::io::{Read, Write, BufRead, BufReader};
use std::sync::Arc;
use tokio::sync::Mutex;

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
    input_schema: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
struct MCPToolCallResult {
    content: Vec<serde_json::Value>,
}

// 완벽한 MCP 클라이언트 구조체
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
        let youtube_process = Command::new("/app/venv/bin/python")
            .arg("youtube_mcp_server.py")
            .current_dir("/app/youtube")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()?;
        
        println!("✅ YouTube MCP 서버 프로세스 생성 성공");
        self.youtube_process = Some(youtube_process);

        // Video MCP 서버 프로세스 생성
        let video_process = Command::new("/app/venv/bin/python")
            .arg("video_mcp_server.py")
            .current_dir("/app/video")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()?;
        
        println!("✅ Video MCP 서버 프로세스 생성 성공");
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

    // MCP 요청 전송 (MCP stdio 프레이밍: Content-Length 헤더 사용)
    async fn send_mcp_request(&mut self, request: &MCPRequest, server_type: &str) -> Result<String, anyhow::Error> {
        let body = serde_json::to_string(request)?;
        let header = format!("Content-Length: {}\r\n\r\n", body.as_bytes().len());
        
        let process = match server_type {
            "youtube" => &mut self.youtube_process,
            "video" => &mut self.video_process,
            _ => return Err(anyhow::anyhow!("알 수 없는 서버 타입: {}", server_type)),
        };

        if let Some(ref mut proc) = process {
            if let Some(stdin) = &mut proc.stdin {
                stdin.write_all(header.as_bytes())?;
                stdin.write_all(body.as_bytes())?;
                stdin.flush()?;
            }
            
            if let Some(stdout) = &mut proc.stdout {
                let mut reader = BufReader::new(stdout);
                // 헤더 읽기
                let mut content_length: Option<usize> = None;
                loop {
                    let mut line = String::new();
                    let n = reader.read_line(&mut line)?;
                    if n == 0 { return Err(anyhow::anyhow!("서버로부터 응답이 없습니다")); }
                    let line_trim = line.trim_end();
                    if line_trim.is_empty() { break; } // 빈 줄(헤더 종료)
                    if let Some(rest) = line_trim.strip_prefix("Content-Length: ") {
                        if let Ok(len) = rest.parse::<usize>() { content_length = Some(len); }
                    }
                }
                let len = content_length.ok_or_else(|| anyhow::anyhow!("Content-Length 헤더가 없습니다"))?;
                let mut buf = vec![0u8; len];
                reader.read_exact(&mut buf)?;
                let response = String::from_utf8(buf)?;
                return Ok(response);
            }
        }

        Err(anyhow::anyhow!("MCP 서버와 통신할 수 없습니다"))
    }

    // MCP 서버 초기화
    async fn initialize_mcp_server(&mut self, server_type: &str) -> Result<String, anyhow::Error> {
        let init_request = MCPRequest {
            jsonrpc: "2.0".to_string(),
            id: "1".to_string(),
            method: "initialize".to_string(),
            params: serde_json::json!({
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": { "name": "rust-mcp-client", "version": "1.0.0" }
            }),
        };
        self.send_mcp_request(&init_request, server_type).await
    }
}

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

#[derive(Clone)]
struct AppState {
    mcp: Arc<Mutex<MCPClient>>, 
}

#[tokio::main]
async fn main() {
    println!("🚀 백엔드(HTTP for UI) + 완벽한 MCP 클라이언트 시작 중...");

    let mut client = MCPClient::new();
    if let Err(e) = client.connect_to_mcp_servers().await {
        eprintln!("⚠️ MCP 서버 프로세스 생성 실패: {}", e);
    }

    let state = AppState { mcp: Arc::new(Mutex::new(client)) };

    // 초기화는 백그라운드에서 수행하여 시작을 막지 않음
    let init_state = state.clone();
    tokio::spawn(async move {
        let mut guard = init_state.mcp.lock().await;
        // YouTube init
        match tokio::time::timeout(std::time::Duration::from_secs(5), guard.initialize_mcp_server("youtube")).await {
            Ok(Ok(resp)) => println!("✅ YouTube initialize 응답: {}", resp),
            Ok(Err(e)) => eprintln!("⚠️ YouTube initialize 실패: {}", e),
            Err(_) => eprintln!("⚠️ YouTube initialize 타임아웃"),
        }
        // Video init
        match tokio::time::timeout(std::time::Duration::from_secs(5), guard.initialize_mcp_server("video")).await {
            Ok(Ok(resp)) => println!("✅ Video initialize 응답: {}", resp),
            Ok(Err(e)) => eprintln!("⚠️ Video initialize 실패: {}", e),
            Err(_) => eprintln!("⚠️ Video initialize 타임아웃"),
        }
    });

    let cors = tower_http::cors::CorsLayer::new()
        .allow_methods([Method::GET, Method::POST])
        .allow_origin(tower_http::cors::Any);

    let app = Router::new()
        .route("/health", get(|| async { "ok" }))
        .route("/", get(|| async { Html(include_str!("../static/index.html")) }))
        .route("/static/app.js", get(|| async { Html(include_str!("../static/app.js")) }))
        .route("/static/style.css", get(|| async { Html(include_str!("../static/style.css")) }))
        .route("/api/youtube/search", post(youtube_search))
        // 채널 분석 API 호환 경로들 (임시 에러 JSON 반환)
        .route("/api/channel-info", post(channel_info))
        .route("/api/channel/info", post(channel_info))
        .with_state(state)
        .layer(cors);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:8080").await.unwrap();
    println!("✅ HTTP(UI) 서버가 8080에서 대기 중 (호스트 3000)");
    axum::serve(listener, app).await.unwrap();
}

async fn youtube_search(State(state): State<AppState>, Json(payload): Json<YouTubeSearchRequest>) -> JsonResponse<YouTubeSearchResponse> {
    let mut guard = state.mcp.lock().await;

    // 안전장치: 요청마다 간단 초기화 시도 (3초 타임아웃, 실패해도 계속 진행)
    let _ = tokio::time::timeout(std::time::Duration::from_secs(3), guard.initialize_mcp_server("youtube")).await;

    let args = serde_json::json!({
        "query": payload.query,
        "max_results": payload.max_results.unwrap_or(5)
    });

    match guard.call_youtube_function("youtube_search", args).await {
        Ok(response) => {
            // JSON-RPC → TextContent 파싱 → 프론트 기대 형태로 변환
            let mut videos: Vec<serde_json::Value> = Vec::new();
            if let Ok(v) = serde_json::from_str::<serde_json::Value>(&response) {
                if let Some(text) = v.get("result").and_then(|r| r.get("content")).and_then(|c| c.get(0)).and_then(|c0| c0.get("text")).and_then(|t| t.as_str()) {
                    // 예: "검색 결과: N개\n1. 타이틀 (길이)\n2. ..."
                    for line in text.lines().skip(1) {
                        if let Some((_, rest)) = line.split_once('.') {
                            let title = rest.trim().trim_matches('-').trim();
                            videos.push(serde_json::json!({
                                "title": title,
                                "channel": "unknown",
                                "views": "-",
                                "likes": "-",
                                "duration": "-",
                                "url": null,
                                "video_id": null
                            }));
                        }
                    }
                }
            }
            JsonResponse(YouTubeSearchResponse { success: true, data: Some(serde_json::json!({"results": videos})), error: None })
        }
        Err(e) => {
            JsonResponse(YouTubeSearchResponse { success: false, data: None, error: Some(format!("MCP 오류: {}", e)) })
        }
    }
} 

#[derive(Debug, Deserialize)]
struct ChannelInfoRequest { video_url: Option<String>, url: Option<String> }

#[derive(Debug, Serialize)]
struct GenericErrorResponse { success: bool, error: String }

async fn channel_info(Json(_payload): Json<ChannelInfoRequest>) -> JsonResponse<GenericErrorResponse> {
    // 아직 MCP 도구 미구현이므로 깔끔한 에러 JSON 반환 (프론트에서 파싱 오류 방지)
    JsonResponse(GenericErrorResponse { success: false, error: "채널 분석 API는 아직 MCP 도구로 연결되지 않았습니다.".to_string() })
} 