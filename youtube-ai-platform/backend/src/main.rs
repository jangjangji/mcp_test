use axum::{
    extract::State,
    extract::Json,
    http::Method,
    response::{Html, Json as JsonResponse},
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;
use reqwest;

// HTTP 기반 MCP 클라이언트 구조체
#[derive(Clone)]
struct MCPHTTPClient {
    youtube_base_url: String,
    video_base_url: String,
}

impl MCPHTTPClient {
    fn new() -> Self {
        Self {
            youtube_base_url: "http://youtube-mcp-server:8001".to_string(),
            video_base_url: "http://video-mcp-server:8002".to_string(),
        }
    }

    // YouTube MCP 도구 호출
    async fn call_youtube_tool(&self, tool_name: &str, args: serde_json::Value) -> Result<String, anyhow::Error> {
        let url = format!("{}/tools/{}", self.youtube_base_url, tool_name);
        
        println!("🚀 YouTube MCP 도구 호출: {} -> {}", tool_name, url);
        
        let client = reqwest::Client::new();
        let response = client.post(&url)
            .json(&args)
            .send()
            .await?;
        
        let status = response.status();
        if status.is_success() {
            let response_text = response.text().await?;
            println!("✅ YouTube MCP 응답: {}", response_text);
            Ok(response_text)
        } else {
            let error_text = response.text().await?;
            println!("❌ YouTube MCP 오류: {}", error_text);
            Err(anyhow::anyhow!("HTTP 오류: {}", status))
        }
    }

    // Video MCP 도구 호출
    async fn call_video_tool(&self, tool_name: &str, args: serde_json::Value) -> Result<String, anyhow::Error> {
        let url = format!("{}/tools/{}", self.video_base_url, tool_name);
        
        println!("🚀 Video MCP 도구 호출: {} -> {}", tool_name, url);
        
        let client = reqwest::Client::new();
        let response = client.post(&url)
            .json(&args)
            .send()
            .await?;
        
        let status = response.status();
        if status.is_success() {
            let response_text = response.text().await?;
            println!("✅ Video MCP 응답: {}", response_text);
            Ok(response_text)
        } else {
            let error_text = response.text().await?;
            println!("❌ Video MCP 오류: {}", error_text);
            Err(anyhow::anyhow!("HTTP 오류: {}", status))
        }
    }

    // MCP 서버 헬스 체크
    async fn health_check(&self) -> Result<(), anyhow::Error> {
        let youtube_url = format!("{}/health", self.youtube_base_url);
        let video_url = format!("{}/health", self.video_base_url);
        
        let client = reqwest::Client::new();
        
        // YouTube MCP 서버 헬스 체크
        match client.get(&youtube_url).send().await {
            Ok(response) if response.status().is_success() => {
                println!("✅ YouTube MCP 서버 정상");
            }
            _ => {
                println!("⚠️ YouTube MCP 서버 연결 실패");
            }
        }
        
        // Video MCP 서버 헬스 체크
        match client.get(&video_url).send().await {
            Ok(response) if response.status().is_success() => {
                println!("✅ Video MCP 서버 정상");
            }
            _ => {
                println!("⚠️ Video MCP 서버 연결 실패");
            }
        }
        
        Ok(())
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
    mcp: Arc<Mutex<MCPHTTPClient>>, 
}

#[derive(Debug, Deserialize)]
struct ChannelInfoRequest { 
    video_url: Option<String>, 
    url: Option<String> 
}

#[derive(Debug, Serialize)]
struct ChannelAnalysisResponse {
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

#[derive(Debug, Deserialize)]
struct TranscriptRequest {
    video_url: String,
}

#[derive(Debug, Serialize)]
struct TranscriptResponse {
    success: bool,
    data: Option<serde_json::Value>,
    error: Option<String>,
}

#[derive(Debug, Deserialize)]
struct SaveVideoRequest {
    video_url: String,
    video_name: Option<String>,
}

#[derive(Debug, Serialize)]
struct SaveVideoResponse {
    success: bool,
    data: Option<serde_json::Value>,
    error: Option<String>,
}

#[derive(Debug, Deserialize)]
struct SearchSimilarRequest {
    query: String,
    top_k: Option<i32>,
}

#[derive(Debug, Serialize)]
struct SearchSimilarResponse {
    success: bool,
    data: Option<serde_json::Value>,
    error: Option<String>,
}

#[derive(Debug, Deserialize)]
struct UploadVideoRequest {
    video_name: String,
}

#[derive(Debug, Serialize)]
struct UploadVideoResponse {
    success: bool,
    data: Option<serde_json::Value>,
    error: Option<String>,
}

#[derive(Debug, Deserialize)]
struct TrendingAnalysisRequest {
    region: Option<String>,
    max_results: Option<i32>,
}

#[derive(Debug, Serialize)]
struct TrendingAnalysisResponse {
    success: bool,
    data: Option<serde_json::Value>,
    error: Option<String>,
}

async fn youtube_search(State(state): State<AppState>, Json(payload): Json<YouTubeSearchRequest>) -> JsonResponse<YouTubeSearchResponse> {
    let guard = state.mcp.lock().await;

    let args = serde_json::json!({
        "query": payload.query,
        "max_results": payload.max_results.unwrap_or(5)
    });

    match guard.call_youtube_tool("youtube_search", args).await {
        Ok(response) => {
            if let Ok(v) = serde_json::from_str::<serde_json::Value>(&response) {
                if let Some(data) = v.get("data") {
                    JsonResponse(YouTubeSearchResponse { 
                        success: true, 
                        data: Some(data.clone()),
                        error: None 
                    })
                } else {
                    JsonResponse(YouTubeSearchResponse { 
                        success: false, 
                        data: None,
                        error: Some("응답 데이터가 없습니다".to_string()) 
                    })
                }
            } else {
                JsonResponse(YouTubeSearchResponse { 
                    success: false, 
                    data: None,
                    error: Some("응답 파싱 실패".to_string()) 
                })
            }
        }
        Err(e) => {
            JsonResponse(YouTubeSearchResponse { 
                success: false, 
                data: None,
                error: Some(format!("MCP 오류: {}", e)) 
            })
        }
    }
}

async fn channel_info(State(state): State<AppState>, Json(payload): Json<ChannelInfoRequest>) -> JsonResponse<ChannelAnalysisResponse> {
    println!("🔍 채널 분석 요청 받음: {:?}", payload);
    
    let guard = state.mcp.lock().await;
    
    // video_url 또는 url에서 URL 추출
    let video_url = match payload.video_url.or(payload.url) {
        Some(url) => {
            println!("🔗 분석할 URL: {}", url);
            url
        },
        None => {
            println!("❌ URL이 제공되지 않음");
            return JsonResponse(ChannelAnalysisResponse { 
                success: false, 
                data: None,
                error: Some("video_url 또는 url이 필요합니다.".to_string()) 
            });
        }
    };
    
    // YouTube MCP 서버의 analyze_channel 도구 호출
    let args = serde_json::json!({
        "video_url": video_url
    });
    
    println!("🚀 MCP 도구 호출 시작: analyze_channel");
    match guard.call_youtube_tool("analyze_channel", args).await {
        Ok(response) => {
            println!("✅ MCP 응답 받음: {}", response);
            
            // JSON 응답 파싱
            if let Ok(v) = serde_json::from_str::<serde_json::Value>(&response) {
                if let Some(data) = v.get("data") {
                    println!("📝 파싱된 데이터: {:?}", data);
                    
                    return JsonResponse(ChannelAnalysisResponse { 
                        success: true, 
                        data: Some(data.clone()),
                        error: None
                    });
                }
            }
            
            println!("⚠️ 응답 파싱 실패, 원본 응답 반환");
            JsonResponse(ChannelAnalysisResponse { 
                success: true, 
                data: Some(serde_json::json!({"raw_response": response})),
                error: None
            })
        }
        Err(e) => {
            println!("❌ MCP 호출 실패: {}", e);
            JsonResponse(ChannelAnalysisResponse { 
                success: false, 
                data: None,
                error: Some(format!("MCP 오류: {}", e)) 
            })
        }
    }
} 

async fn video_search(State(state): State<AppState>, Json(payload): Json<VideoSearchRequest>) -> JsonResponse<VideoSearchResponse> {
    println!("🔍 비디오 검색 요청 받음: {:?}", payload);
    
    let guard = state.mcp.lock().await;
    
    // Video MCP 서버의 video_search 도구 호출
    let args = serde_json::json!({
        "query": payload.query,
        "top_k": payload.top_k.unwrap_or(5)
    });
    
    println!("🚀 Video MCP 도구 호출 시작: video_search");
    match guard.call_video_tool("video_search", args).await {
        Ok(response) => {
            println!("✅ Video MCP 응답 받음: {}", response);
            
            // Video MCP 서버의 응답을 구조화된 데이터로 변환
            let search_results = parse_video_search_response(&response);
            
            JsonResponse(VideoSearchResponse { 
                success: true, 
                data: Some(serde_json::json!({
                    "query": payload.query,
                    "results": search_results,
                    "total_count": search_results.len()
                })),
                error: None
            })
        }
        Err(e) => {
            println!("❌ Video MCP 호출 실패: {}", e);
            JsonResponse(VideoSearchResponse { 
                success: false, 
                data: None,
                error: Some(format!("Video MCP 오류: {}", e))
            })
        }
    }
}

// Video MCP 서버의 응답을 파싱하는 헬퍼 함수
fn parse_video_search_response(response: &str) -> Vec<serde_json::Value> {
    // Video MCP 서버는 JSON 형태로 응답: {"success":true,"data":{"result":"검색 결과: 2개\n1. dog_video - 00:00:05 (유사도: 0.996)\n2. dog_video - 00:00:07 (유사도: 0.928)"}}
    let mut results = Vec::new();
    
    // JSON 응답 파싱
    if let Ok(json_response) = serde_json::from_str::<serde_json::Value>(response) {
        if let Some(data) = json_response.get("data") {
            if let Some(result_str) = data.get("result").and_then(|r| r.as_str()) {
                println!("🔍 파싱할 문자열: {}", result_str);
                
                // 줄바꿈으로 분리
                let lines: Vec<&str> = result_str.lines().collect();
                
                for line in lines {
                    if line.contains('.') && line.contains('-') {
                        // "1. dog_video - 00:00:05 (유사도: 0.996)" 형태 파싱
                        let parts: Vec<&str> = line.split('-').collect();
                        if parts.len() >= 2 {
                            let video_info = parts[0].trim();
                            let time_similarity = parts[1].trim();
                            
                            // 비디오 이름 추출 (숫자와 점 제거)
                            let video_name = video_info.split('.').nth(1).unwrap_or("").trim();
                            println!("📹 비디오 이름: {}", video_name);
                            
                            // 시간과 유사도 추출
                            let time_similarity_parts: Vec<&str> = time_similarity.split('(').collect();
                            let timestamp = time_similarity_parts[0].trim();
                            let similarity_str = time_similarity_parts.get(1)
                                .and_then(|s| s.strip_suffix(')'))
                                .and_then(|s| s.split(':').nth(1))
                                .unwrap_or("0.0")
                                .trim();
                            
                            let similarity: f64 = similarity_str.parse().unwrap_or(0.0);
                            println!("⏰ 시간: {}, 유사도: {}", timestamp, similarity);
                            
                            let result = serde_json::json!({
                                "video_name": video_name,
                                "title": format!("{} 비디오", video_name), // 제목 추가
                                "timestamp": timestamp,
                                "similarity": similarity,
                                "description": format!("{}에서 발견된 장면", video_name)
                            });
                            
                            results.push(result);
                        }
                    }
                }
            }
        }
    }
    
    println!("📝 파싱된 검색 결과: {:?}", results);
    results
}

async fn transcript_extraction(State(state): State<AppState>, Json(payload): Json<TranscriptRequest>) -> JsonResponse<TranscriptResponse> {
    println!("📝 자막 추출 요청 받음: {:?}", payload);
    
    // 자막 추출은 YouTube MCP 서버에서 처리
    let guard = state.mcp.lock().await;
    
    let args = serde_json::json!({
        "video_url": payload.video_url
    });
    
    // YouTube MCP 서버에 자막 추출 요청 (실제로는 구현 필요)
    JsonResponse(TranscriptResponse { 
        success: true, 
        data: Some(serde_json::json!({
            "message": "자막 추출 기능은 아직 구현되지 않았습니다",
            "video_url": payload.video_url
        })),
        error: None
    })
}

async fn save_video(State(state): State<AppState>, Json(payload): Json<SaveVideoRequest>) -> JsonResponse<SaveVideoResponse> {
    println!("💾 비디오 저장 요청 받음: {:?}", payload);
    
    // Video MCP 서버에 비디오 저장 요청
    let guard = state.mcp.lock().await;
    
    let args = serde_json::json!({
        "video_path": payload.video_url,
        "video_name": payload.video_name.unwrap_or_else(|| "unnamed_video".to_string())
    });
    
    match guard.call_video_tool("add_video", args).await {
        Ok(response) => {
            JsonResponse(SaveVideoResponse { 
                success: true, 
                data: Some(serde_json::json!({"message": "비디오 저장 완료", "response": response})),
                error: None
            })
        }
        Err(e) => {
            JsonResponse(SaveVideoResponse { 
                success: false, 
                data: None,
                error: Some(format!("비디오 저장 실패: {}", e))
            })
        }
    }
}

async fn search_similar(State(state): State<AppState>, Json(payload): Json<SearchSimilarRequest>) -> JsonResponse<SearchSimilarResponse> {
    println!("🔍 유사도 검색 요청 받음: {:?}", payload);
    
    // Video MCP 서버에 유사도 검색 요청
    let guard = state.mcp.lock().await;
    
    let args = serde_json::json!({
        "query": payload.query,
        "top_k": payload.top_k.unwrap_or(5)
    });
    
    match guard.call_video_tool("video_search", args).await {
        Ok(response) => {
            JsonResponse(SearchSimilarResponse { 
                success: true, 
                data: Some(serde_json::json!({"response": response})),
                error: None
            })
        }
        Err(e) => {
            JsonResponse(SearchSimilarResponse { 
                success: false, 
                data: None,
                error: Some(format!("유사도 검색 실패: {}", e))
            })
        }
    }
}

async fn upload_video(State(state): State<AppState>, Json(payload): Json<UploadVideoRequest>) -> JsonResponse<UploadVideoResponse> {
    println!("📤 비디오 업로드 요청 받음: {:?}", payload);
    
    // 비디오 업로드 처리 (실제로는 파일 업로드 로직 필요)
    JsonResponse(UploadVideoResponse { 
        success: true, 
        data: Some(serde_json::json!({
            "message": "비디오 업로드 완료",
            "video_name": payload.video_name
        })),
        error: None
    })
}

async fn trending_analysis(State(state): State<AppState>, Json(payload): Json<TrendingAnalysisRequest>) -> JsonResponse<TrendingAnalysisResponse> {
    println!("📊 트렌딩 분석 요청 받음: {:?}", payload);
    
    // YouTube MCP 서버에 트렌딩 분석 요청
    let guard = state.mcp.lock().await;
    
    let region = payload.region.unwrap_or_else(|| "KR".to_string());
    let max_results = payload.max_results.unwrap_or(10);
    
    let args = serde_json::json!({
        "region": region.clone(),
        "max_results": max_results
    });
    
    // YouTube MCP 서버에 트렌딩 분석 요청 (실제로는 구현 필요)
    JsonResponse(TrendingAnalysisResponse { 
        success: true, 
        data: Some(serde_json::json!({
            "message": "트렌딩 분석 기능은 아직 구현되지 않았습니다",
            "region": region,
            "max_results": max_results
        })),
        error: None
    })
}

#[tokio::main]
async fn main() {
    println!("🚀 백엔드(HTTP for UI) + HTTP 기반 MCP 클라이언트 시작 중...");

    let client = MCPHTTPClient::new();
    
    // 백그라운드에서 MCP 서버 헬스 체크
    let health_client = client.clone();
    tokio::spawn(async move {
        tokio::time::sleep(tokio::time::Duration::from_secs(5)).await;
        if let Err(e) = health_client.health_check().await {
            eprintln!("⚠️ MCP 서버 헬스 체크 실패: {}", e);
        }
    });

    let state = AppState { 
        mcp: Arc::new(Mutex::new(client)),
    };

    let cors = tower_http::cors::CorsLayer::new()
        .allow_methods([Method::GET, Method::POST])
        .allow_origin(tower_http::cors::Any);

    let app = Router::new()
        .route("/health", get(|| async { "ok" }))
        .route("/", get(|| async { Html(include_str!("../static/index.html")) }))
        .route("/static/app.js", get(|| async { Html(include_str!("../static/app.js")) }))
        .route("/static/style.css", get(|| async { Html(include_str!("../static/style.css")) }))
        .route("/api/youtube/search", post(youtube_search))
        .route("/api/search-video", post(video_search))
        .route("/api/channel-info", post(channel_info))
        .route("/api/channel/info", post(channel_info))
        .route("/api/transcript", post(transcript_extraction))
        .route("/api/transcript-extraction", post(transcript_extraction))
        .route("/api/save-single-video", post(save_video))
        .route("/api/save-video", post(save_video))
        .route("/api/search-similar", post(search_similar))
        .route("/api/upload-video", post(upload_video))
        .route("/api/trending-analysis", post(trending_analysis))
        .with_state(state)
        .layer(cors);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:8080").await.unwrap();
    println!("✅ HTTP(UI) 서버가 8080에서 대기 중 (호스트 3000)");
    axum::serve(listener, app).await.unwrap();
} 