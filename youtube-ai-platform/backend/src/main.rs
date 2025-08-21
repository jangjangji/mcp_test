// 웹 서버를 만들기 위한 필요한 라이브러리들을 가져오기
use axum::{  // axum: 웹 서버 프레임워크
    extract::State,      // State: 서버 상태 정보를 가져오는 기능
    extract::Json,       // Json: JSON 데이터를 가져오는 기능  
    extract::Multipart,  // Multipart: multipart/form-data 데이터 처리
    http::Method,        // Method: HTTP 메서드(GET, POST 등) 정의
    response::{Html, Json as JsonResponse},  // response: 응답 타입들 (Html, Json)
    routing::{get, post},  // routing: 라우팅 기능(GET, POST 요청 처리)
    Router,              // Router: 라우터(URL 경로와 함수를 연결하는 역할)
};
use serde::{Deserialize, Serialize};  // serde: JSON 변환을 위한 라이브러리
use std::sync::Arc;      // Arc: 여러 스레드에서 안전하게 데이터 공유
use tokio::sync::Mutex;  // Mutex: 비동기 환경에서 데이터 보호 (한 번에 하나만 접근)
use reqwest;             // reqwest: HTTP 클라이언트(다른 서버에 요청 보내기)

// HTTP 기반 MCP 클라이언트 구조체 정의
// MCP = Model Context Protocol (AI 모델과 도구를 연결하는 프로토콜)
#[derive(Clone)]  // Clone: 이 구조체를 복사할 수 있게 만듦
struct MCPHTTPClient {
    youtube_base_url: String,  // YouTube MCP 서버 주소 저장 (예: "http://youtube-mcp-server:8001")
    video_base_url: String,    // Video MCP 서버 주소 저장 (예: "http://video-mcp-server:8002")
}

// MCPHTTPClient에 기능을 추가하는 구현 블록
impl MCPHTTPClient {
    // 새로운 MCP 클라이언트를 만드는 함수
    fn new() -> Self {  // Self는 MCPHTTPClient를 의미
        Self {  // 새로운 MCPHTTPClient 인스턴스 생성
            youtube_base_url: "http://youtube-mcp-server:8001".to_string(),  // YouTube MCP 서버 주소
            video_base_url: "http://video-mcp-server:8002".to_string(),      // Video MCP 서버 주소
        }
    }

    // YouTube MCP 도구 호출 함수
    // tool_name: 호출할 도구 이름 (예: "youtube_search")
    // args: 도구에 전달할 데이터 (JSON 형태)
    // Result<String, anyhow::Error>: 성공하면 String, 실패하면 Error 반환
    async fn call_tool(&self, base_url: &str, tool_name: &str, args: serde_json::Value) -> Result<String, anyhow::Error> {
        // URL 만들기: "http://youtube-mcp-server:8001/tools/youtube_search"
        let url = format!("{}/tools/{}", base_url, tool_name);
        
        // 로그 출력: 어떤 도구를 어떤 URL로 호출하는지 표시
        println!("🚀 MCP 도구 호출: {} -> {}", tool_name, url);
        
        // HTTP 클라이언트 만들기
        let client = reqwest::Client::new();
        
        // POST 요청 보내기
        let response = client.post(&url)      // POST 요청 생성
            .json(&args)                      // JSON 데이터 첨부
            .send()                           // 요청 전송
            .await?;                          // 응답 기다리기 (실패하면 에러 반환)
        
        // HTTP 상태 코드 확인 (200번대면 성공)
        let status = response.status();
        if status.is_success() {              // 성공 상태 코드인지 확인
            let response_text = response.text().await?;  // 응답 내용을 텍스트로 변환
            println!("✅ MCP 응답: {}", response_text);  // 성공 로그 출력
            Ok(response_text)                 // 성공 결과 반환
        } else {
            let error_text = response.text().await?;     // 에러 응답 내용 가져오기
            println!("❌ MCP 오류: {}", error_text);  // 에러 로그 출력
            Err(anyhow::anyhow!("HTTP 오류: {}", status))  // 에러 반환
        }
    }

    // Video MCP 도구 호출 함수 (YouTube와 거의 동일한 구조)
    async fn call_video_tool(&self, tool_name: &str, args: serde_json::Value) -> Result<String, anyhow::Error> {
        // Video MCP 서버 URL 만들기
        let url = format!("{}/tools/{}", self.video_base_url, tool_name);
        
        // 로그 출력
        println!("🚀 Video MCP 도구 호출: {} -> {}", tool_name, url);
        
        // HTTP 클라이언트 만들기
        let client = reqwest::Client::new();
        
        // POST 요청 보내기
        let response = client.post(&url)
            .json(&args)
            .send()
            .await?;
        
        // 응답 상태 확인
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

    // MCP 서버 헬스 체크 함수 (서버가 살아있는지 확인)
    async fn health_check(&self) -> Result<(), anyhow::Error> {
        // 헬스 체크 URL 만들기
        let youtube_url = format!("{}/health", self.youtube_base_url);  // YouTube MCP 헬스 체크 URL
        let video_url = format!("{}/health", self.video_base_url);      // Video MCP 헬스 체크 URL
        
        // HTTP 클라이언트 만들기
        let client = reqwest::Client::new();
        
        // YouTube MCP 서버 헬스 체크
        match client.get(&youtube_url).send().await {  // GET 요청으로 헬스 체크
            Ok(response) if response.status().is_success() => {  // 성공하면
                println!("✅ YouTube MCP 서버 정상");
            }
            _ => {  // 실패하면
                println!("⚠️ YouTube MCP 서버 연결 실패");
            }
        }
        
        // Video MCP 서버 헬스 체크 (동일한 방식)
        match client.get(&video_url).send().await {
            Ok(response) if response.status().is_success() => {
                println!("✅ Video MCP 서버 정상");
            }
            _ => {
                println!("⚠️ Video MCP 서버 연결 실패");
            }
        }
        
        Ok(())  // 성공 반환
    }
}

// YouTube 검색 요청 구조체 (프론트엔드에서 보내는 데이터 형태)
#[derive(Debug, Deserialize)]  // Debug: 출력 가능, Deserialize: JSON에서 변환 가능
struct YouTubeSearchRequest {
    query: String,           // 검색어 (예: "강아지")
    max_results: Option<i32>, // 최대 결과 수 (선택사항, 없으면 기본값 사용)
}

// YouTube 검색 응답 구조체 (프론트엔드로 보내는 데이터 형태)
#[derive(Debug, Serialize)]   // Serialize: JSON으로 변환 가능
struct YouTubeSearchResponse {
    success: bool,                              // 성공 여부 (true/false)
    data: Option<serde_json::Value>,           // 데이터 (선택사항, 성공시에만)
    error: Option<String>,                      // 에러 메시지 (선택사항, 실패시에만)
}

// 앱 상태 구조체 (서버 전체에서 공유하는 데이터)
#[derive(Clone)]  // Clone: 복사 가능
struct AppState {
    mcp: Arc<Mutex<MCPHTTPClient>>,  // MCP 클라이언트를 여러 스레드에서 안전하게 공유
    // Arc: 여러 스레드에서 데이터 공유 가능
    // Mutex: 한 번에 하나의 스레드만 접근 가능하게 보호
}

// 채널 정보 요청 구조체
#[derive(Debug, Deserialize)] 
struct ChannelInfoRequest { 
    video_url: Option<String>,  // 비디오 URL (선택사항)
    url: Option<String>         // 일반 URL (선택사항)
}

// 채널 분석 응답 구조체
#[derive(Debug, Serialize)]
struct ChannelAnalysisResponse {
    success: bool,                              // 성공 여부
    data: Option<serde_json::Value>,           // 데이터
    error: Option<String>,                      // 에러 메시지
}

// 비디오 검색 요청 구조체 (프론트엔드에서 보내는 데이터 형태)
#[derive(Debug, Deserialize)]
struct VideoSearchRequest {
    query: String,        // 검색어 (예: "강아지 헤엄치는 장면")
    top_k: Option<i32>,   // 상위 K개 결과 (선택사항, 없으면 기본값 사용)
}

// 비디오 검색 응답 구조체 (프론트엔드로 보내는 데이터 형태)
#[derive(Debug, Serialize)]
struct VideoSearchResponse {
    success: bool,                              // 성공 여부
    data: Option<serde_json::Value>,           // 데이터
    error: Option<String>,                      // 에러 메시지
}

// 자막 추출 요청 구조체
#[derive(Debug, Deserialize)]
struct TranscriptRequest {
    video_url: String,    // 비디오 URL
}

// 자막 추출 응답 구조체
#[derive(Debug, Serialize)]
struct TranscriptResponse {
    success: bool,                              // 성공 여부
    data: Option<serde_json::Value>,           // 데이터
    error: Option<String>,                      // 에러 메시지
}

// 비디오 저장 요청 구조체
#[derive(Debug, Deserialize)]
struct SaveVideoRequest {
    video_url: String,        // 비디오 URL
    video_name: Option<String>, // 비디오 이름 (선택사항)
}

// 비디오 저장 응답 구조체
#[derive(Debug, Serialize)]
struct SaveVideoResponse {
    success: bool,                              // 성공 여부
    data: Option<serde_json::Value>,           // 데이터
    error: Option<String>,                      // 에러 메시지
}

// 유사도 검색 요청 구조체
#[derive(Debug, Deserialize)]
struct SearchSimilarRequest {
    query: String,        // 검색어
    top_k: Option<i32>,   // 상위 K개 결과
}

// 유사도 검색 응답 구조체
#[derive(Debug, Serialize)]
struct SearchSimilarResponse {
    success: bool,                              // 성공 여부
    data: Option<serde_json::Value>,           // 데이터
    error: Option<String>,                      // 에러 메시지
}

// 비디오 업로드 요청 구조체
#[derive(Debug, Deserialize)]
struct UploadVideoRequest {
    video_name: String,    // 비디오 이름
}

// 비디오 업로드 응답 구조체
#[derive(Debug, Serialize)]
struct UploadVideoResponse {
    success: bool,                              // 성공 여부
    data: Option<serde_json::Value>,           // 데이터
    error: Option<String>,                      // 에러 메시지
}

// 트렌딩 분석 요청 구조체
#[derive(Debug, Deserialize)]
struct TrendingAnalysisRequest {
    region: Option<String>,     // 지역 (선택사항)
    max_results: Option<i32>,   // 최대 결과 수
}

// 트렌딩 분석 응답 구조체
#[derive(Debug, Serialize)]
struct TrendingAnalysisResponse {
    success: bool,                              // 성공 여부
    data: Option<serde_json::Value>,           // 데이터
    error: Option<String>,                      // 에러 메시지
}

// YouTube 검색 함수 (프론트엔드에서 YouTube 검색 요청을 처리)
async fn youtube_search(State(state): State<AppState>, Json(payload): Json<YouTubeSearchRequest>) -> JsonResponse<YouTubeSearchResponse> {
    // State(state): 서버 상태 정보 가져오기
    // Json(payload): JSON 요청 데이터 가져오기
    // -> JsonResponse<YouTubeSearchResponse>: JSON 응답 반환
    
    let guard = state.mcp.lock().await;  // MCP 클라이언트 잠금 해제 (사용 가능하게)

    // YouTube MCP 서버에 전달할 데이터 만들기
    let args = serde_json::json!({
        "query": payload.query,          // 검색어
        "max_results": payload.max_results.unwrap_or(5)  // 최대 결과 수 (없으면 5)
    });

    // YouTube MCP 서버 호출
    match guard.call_tool("youtube-mcp-server", "youtube_search", args).await {
        Ok(response) => {  // 성공하면
            // JSON 응답 파싱 시도
            if let Ok(v) = serde_json::from_str::<serde_json::Value>(&response) {
                // "data" 필드가 있으면
                if let Some(data) = v.get("data") {
                    // 성공 응답 반환
                    JsonResponse(YouTubeSearchResponse { 
                        success: true, 
                        data: Some(data.clone()),  // 데이터 복사
                        error: None 
                    })
                } else {  // "data" 필드가 없으면
                    // 실패 응답 반환
                    JsonResponse(YouTubeSearchResponse { 
                        success: false, 
                        data: None,
                        error: Some("응답 데이터가 없습니다".to_string()) 
                    })
                }
            } else {  // JSON 파싱 실패
                JsonResponse(YouTubeSearchResponse { 
                    success: false, 
                    data: None,
                    error: Some("응답 파싱 실패".to_string()) 
                })
            }
        }
        Err(e) => {  // MCP 호출 실패
            JsonResponse(YouTubeSearchResponse { 
                success: false, 
                data: None,
                error: Some(format!("MCP 오류: {}", e)) 
            })
        }
    }
}

// 채널 정보 분석 함수 (프론트엔드에서 채널 분석 요청을 처리)
async fn channel_info(State(state): State<AppState>, Json(payload): Json<ChannelInfoRequest>) -> JsonResponse<ChannelAnalysisResponse> {
    println!("🔍 채널 분석 요청 받음: {:?}", payload);  // 로그 출력
    
    let guard = state.mcp.lock().await;  // MCP 클라이언트 사용 가능하게
    
    // video_url 또는 url에서 URL 추출
    let video_url = match payload.video_url.or(payload.url) {
        Some(url) => {  // URL이 있으면
            println!("🔗 분석할 URL: {}", url);  // 로그 출력
            url
        },
        None => {  // URL이 없으면
            println!("❌ URL이 제공되지 않음");  // 에러 로그
            return JsonResponse(ChannelAnalysisResponse {  // 에러 응답 반환
                success: false, 
                data: None,
                error: Some("video_url 또는 url이 필요합니다.".to_string())
            });
        }
    };
    
    // YouTube MCP 서버의 analyze_channel 도구 호출
    let args = serde_json::json!({
        "video_url": video_url  // 분석할 비디오 URL
    });
    
    println!("🚀 MCP 도구 호출 시작: analyze_channel");  // 로그 출력
    
    // YouTube MCP 서버 호출
    match guard.call_tool("youtube-mcp-server", "analyze_channel", args).await {
        Ok(response) => {  // 성공하면
            println!("✅ MCP 응답 받음: {}", response);  // 응답 로그
            
            // JSON 응답 파싱 시도
            if let Ok(v) = serde_json::from_str::<serde_json::Value>(&response) {
                if let Some(data) = v.get("data") {  // "data" 필드가 있으면
                    println!("📝 파싱된 데이터: {:?}", data);  // 파싱된 데이터 로그
                    
                    // 성공 응답 반환
                    return JsonResponse(ChannelAnalysisResponse { 
                        success: true, 
                        data: Some(data.clone()),  // 데이터 복사
                        error: None
                    });
                }
            }
            
            // 응답 파싱 실패시 원본 응답 반환
            println!("⚠️ 응답 파싱 실패, 원본 응답 반환");
            JsonResponse(ChannelAnalysisResponse { 
                success: true, 
                data: Some(serde_json::json!({"raw_response": response})),  // 원본 응답 저장
                error: None
            })
        }
        Err(e) => {  // MCP 호출 실패
            println!("❌ MCP 호출 실패: {}", e);  // 에러 로그
            JsonResponse(ChannelAnalysisResponse { 
                success: false, 
                data: None,
                error: Some(format!("MCP 오류: {}", e)) 
            })
        }
    }
} 

// 비디오 검색 함수 (프론트엔드에서 비디오 검색 요청을 처리) - 핵심 함수!
async fn video_search(State(state): State<AppState>, Json(payload): Json<VideoSearchRequest>) -> JsonResponse<VideoSearchResponse> {
    println!("🔍 비디오 검색 요청 받음: {:?}", payload);  // 로그 출력
    
    let guard = state.mcp.lock().await;  // MCP 클라이언트 사용 가능하게
    
    // Video MCP 서버에 전달할 데이터 만들기
    let args = serde_json::json!({
        "query": payload.query,                    // 검색어 (예: "강아지 헤엄치는 장면")
        "top_k": payload.top_k.unwrap_or(5)       // 상위 K개 (없으면 5)
    });
    
    println!("🚀 Video MCP 도구 호출 시작: video_search");  // 로그 출력
    
    // Video MCP 서버 호출
    match guard.call_video_tool("video_search", args).await {
        Ok(response) => {  // 성공하면
            println!("✅ Video MCP 응답 받음: {}", response);  // 응답 로그
            
            // Video MCP 서버의 응답을 구조화된 데이터로 변환
            let search_results = parse_video_search_response(&response);  // 파싱 함수 호출
            
            // 성공 응답 반환
            JsonResponse(VideoSearchResponse { 
                success: true, 
                data: Some(serde_json::json!({  // JSON 데이터 만들기
                    "query": payload.query,      // 검색어
                    "results": search_results,   // 파싱된 결과
                    "total_count": search_results.len()  // 결과 개수
                })),
                error: None
            })
        }
        Err(e) => {  // 실패하면
            println!("❌ Video MCP 호출 실패: {}", e);  // 에러 로그
            JsonResponse(VideoSearchResponse {  // 실패 응답 반환
                success: false, 
                data: None,
                error: Some(format!("Video MCP 오류: {}", e))
            })
        }
    }
}

// Video MCP 서버의 응답을 파싱하는 헬퍼 함수
// response: Video MCP 서버에서 받은 JSON 문자열
// -> Vec<serde_json::Value>: 파싱된 결과 배열 반환
fn parse_video_search_response(response: &str) -> Vec<serde_json::Value> {
    let mut results = Vec::new();
    
    // JSON 응답 파싱 시도
    if let Ok(json_response) = serde_json::from_str::<serde_json::Value>(response) {
        if let Some(data) = json_response.get("data") {
            if let Some(result_str) = data.get("result").and_then(|r| r.as_str()) {
                println!("🔍 파싱할 문자열: {}", result_str);
                
                // 각 줄을 처리
                for line in result_str.lines() {
                    // "1. dog - 00:00:08 (유사도: 1.000)" 형태 파싱
                    if line.contains("(유사도:") && line.contains(" - ") {
                        // 정규식 없이 안전한 문자열 파싱
                        if let Some(dash_pos) = line.rfind(" - ") {
                            let before_dash = &line[..dash_pos];
                            let after_dash = &line[dash_pos + 3..];
                            
                            // 비디오 이름 추출 (숫자와 점 제거)
                            let video_name = if let Some(dot_pos) = before_dash.find(". ") {
                                &before_dash[dot_pos + 2..]
                            } else {
                                before_dash
                            }.trim();
                            
                            // 시간과 유사도 분리
                            if let Some(paren_pos) = after_dash.find(" (유사도: ") {
                                let timestamp = &after_dash[..paren_pos];
                                let similarity_part = &after_dash[paren_pos + " (유사도: ".len()..];
                                let similarity_str = similarity_part.trim_end_matches(')').trim();
                                
                                // 시간 형식 검증 (HH:MM:SS)
                                if timestamp.matches(':').count() == 2 {
                                    if let Ok(similarity) = similarity_str.parse::<f64>() {
                                        println!("📹 비디오 이름: {}, 시간: {}, 유사도: {}", video_name, timestamp, similarity);
                                        
                                        // 결과 객체 생성
                                        let result = serde_json::json!({
                                            "video_name": video_name,
                                            "title": format!("{} 비디오", video_name),
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
            }
        }
    }
    
    println!("📝 파싱된 검색 결과: {}개", results.len());
    results
}

// 자막 추출 함수 (아직 구현되지 않음)
async fn transcript_extraction(State(state): State<AppState>, Json(payload): Json<TranscriptRequest>) -> JsonResponse<TranscriptResponse> {
    println!("📝 자막 추출 요청 받음: {:?}", payload);  // 로그 출력
    
    // 자막 추출은 YouTube MCP 서버에서 처리 (아직 구현되지 않음)
    let _guard = state.mcp.lock().await;  // MCP 클라이언트 사용 가능하게
    
    let _args = serde_json::json!({
        "video_url": payload.video_url  // 비디오 URL
    });
    
    // YouTube MCP 서버에 자막 추출 요청 (실제로는 구현 필요)
    JsonResponse(TranscriptResponse { 
        success: true, 
        data: Some(serde_json::json!({
            "message": "자막 추출 기능은 아직 구현되지 않았습니다",  // 임시 메시지
            "video_url": payload.video_url
        })),
        error: None
    })
}

// 비디오 저장 함수
async fn save_video(State(state): State<AppState>, Json(payload): Json<SaveVideoRequest>) -> JsonResponse<SaveVideoResponse> {
    println!("💾 비디오 저장 요청 받음: {:?}", payload);  // 로그 출력
    
    // Video MCP 서버에 비디오 저장 요청
    let guard = state.mcp.lock().await;  // MCP 클라이언트 사용 가능하게
    
    let args = serde_json::json!({
        "video_path": payload.video_url,  // 비디오 경로
        "video_name": payload.video_name.unwrap_or_else(|| "unnamed_video".to_string())  // 비디오 이름 (없으면 기본값)
    });
    
    // Video MCP 서버 호출
    match guard.call_video_tool("add_video", args).await {
        Ok(result) => {
            println!("✅ Video MCP 서버 응답: {:?}", result);
            JsonResponse(SaveVideoResponse { 
                success: true, 
                data: Some(serde_json::json!({"message": "비디오 저장 완료", "response": result})),
                error: None
            })
        }
        Err(e) => {
            eprintln!("❌ Video MCP 서버 오류: {}", e);
            JsonResponse(SaveVideoResponse { 
                success: false, 
                data: None,
                error: Some(format!("Video MCP 서버 오류: {}", e))
            })
        }
    }
}

// 유사도 검색 함수
async fn search_similar(State(state): State<AppState>, Json(payload): Json<SearchSimilarRequest>) -> JsonResponse<SearchSimilarResponse> {
    println!("🔍 유사도 검색 요청 받음: {:?}", payload);  // 로그 출력
    
    // Video MCP 서버에 유사도 검색 요청
    let guard = state.mcp.lock().await;  // MCP 클라이언트 사용 가능하게
    
    let args = serde_json::json!({
        "query": payload.query,        // 검색어
        "top_k": payload.top_k.unwrap_or(5)  // 상위 K개 (없으면 5)
    });
    
    // Video MCP 서버 호출
    match guard.call_video_tool("video_search", args).await {
        Ok(response) => {  // 성공하면
            JsonResponse(SearchSimilarResponse { 
                success: true, 
                data: Some(serde_json::json!({"response": response})),
                error: None
            })
        }
        Err(e) => {  // 실패하면
            JsonResponse(SearchSimilarResponse { 
                success: false, 
                data: None,
                error: Some(format!("유사도 검색 실패: {}", e))
            })
        }
    }
}

// 비디오 업로드 함수 (multipart/form-data 처리)
async fn upload_video(State(state): State<AppState>, mut multipart: Multipart) -> JsonResponse<UploadVideoResponse> {
    println!("📤 비디오 업로드 요청 받음");
    
    // multipart 데이터에서 파일과 정보 추출
    let mut video_path = String::new();
    let mut video_name = String::new();
    
    // 모든 필드를 처리
    println!("🔍 multipart 필드 처리 시작...");
    
    // multipart 파싱 시도 (더 안전한 방식)
    let mut field_count = 0;
    let mut multipart_parse_error = false;
    
    loop {
        match multipart.next_field().await {
            Ok(Some(mut field)) => {
                field_count += 1;
                let field_name = match field.name() {
                    Some(name) => name.to_string(),
                    None => {
                        println!("⚠️ 이름 없는 필드 발견, 건너뛰기");
                        let _ = field.bytes().await;
                        continue;
                    }
                };
                
                println!("🔍 필드 발견: '{}'", field_name);
                
                match field_name.as_str() {
                    "video" => {
                        println!("📁 비디오 파일 필드 발견");
                        println!("🔍 video 필드 상세 정보:");
                        println!("  - field_name: '{}'", field_name);
                        println!("  - content_type: {:?}", field.content_type());
                        println!("  - file_name: {:?}", field.file_name());
                        
                        // 스트리밍 방식으로 파일을 직접 디스크에 저장
                        let mut chunk_count = 0;
                        let mut total_bytes = 0;
                        let mut has_error = false;
                        
                        // 임시 파일 경로 생성
                        let temp_video_path = format!("uploads/{}.tmp", video_path.split('/').last().unwrap_or("video"));
                        println!("💾 스트리밍 저장 시작: {}", temp_video_path);
                        
                        // 파일 생성
                        let mut file = match std::fs::File::create(&temp_video_path) {
                            Ok(file) => file,
                            Err(e) => {
                                println!("❌ 임시 파일 생성 실패: {}", e);
                                has_error = true;
                                break;
                            }
                        };
                        
                        loop {
                            match field.chunk().await {
                                Ok(Some(bytes)) => {
                                    // 청크를 직접 파일에 쓰기
                                    match std::io::Write::write_all(&mut file, &bytes) {
                                        Ok(_) => {
                                            chunk_count += 1;
                                            total_bytes += bytes.len();
                                            if chunk_count % 10 == 0 {
                                                println!("📦 청크 {} 처리 완료, 현재 크기: {} bytes", chunk_count, total_bytes);
                                            }
                                        }
                                        Err(e) => {
                                            println!("❌ 청크 {} 쓰기 실패: {}", chunk_count, e);
                                            has_error = true;
                                            break;
                                        }
                                    }
                                }
                                Ok(None) => {
                                    println!("✅ 모든 청크 처리 완료");
                                    break;
                                }
                                Err(e) => {
                                    println!("❌ 청크 {} 읽기 실패: {}", chunk_count, e);
                                    has_error = true;
                                    // 오류가 발생해도 지금까지 쓴 데이터는 유지
                                    break;
                                }
                            }
                        }
                        
                        // 파일 닫기
                        drop(file);
                        
                        // 파일 읽기 결과 요약
                        if has_error {
                            println!("⚠️ 파일 읽기/쓰기 도중 에러 발생 ({} bytes 저장됨)", total_bytes);
                        } else {
                            println!("✅ 파일 읽기/쓰기 완료 (총 {} bytes)", total_bytes);
                        }
                        
                        if total_bytes > 0 {
                            // 임시 파일을 최종 파일로 이동
                            video_path = format!("uploads/{}.mp4", video_name.split('.').next().unwrap_or("video"));
                            if let Err(e) = std::fs::rename(&temp_video_path, &video_path) {
                                println!("❌ 파일 이동 실패: {}", e);
                                // 이동 실패 시 임시 파일 삭제
                                let _ = std::fs::remove_file(&temp_video_path);
                            } else {
                                println!("✅ 파일 저장 완료: {} ({} bytes)", video_path, total_bytes);
                            }
                        } else {
                            println!("❌ 파일 데이터가 없음");
                            // 임시 파일 삭제
                            let _ = std::fs::remove_file(&temp_video_path);
                        }
                    }
                    "video_id" => {
                        println!("🆔 video_id 필드 읽기 시도...");
                        match field.text().await {
                            Ok(id) => {
                                video_path = format!("uploads/{}.mp4", id);
                                println!("✅ video_id 읽기 성공: '{}'", id);
                            }
                            Err(e) => {
                                println!("❌ video_id 필드 읽기 실패: {}", e);
                            }
                        }
                    }
                    "original_filename" => {
                        println!("📝 original_filename 필드 읽기 시도...");
                        match field.text().await {
                            Ok(filename) => {
                                video_name = filename.clone();
                                println!("✅ original_filename 읽기 성공: '{}'", filename);
                            }
                            Err(e) => {
                                println!("❌ original_filename 읽기 실패: {}", e);
                            }
                        }
                    }
                    _ => {
                        println!("⚠️ 알 수 없는 필드: '{}'", field_name);
                        let _ = field.bytes().await;
                    }
                }
            }
            Ok(None) => {
                println!("✅ 모든 필드 처리 완료 (총 {}개 필드)", field_count);
                break;
            }
            Err(e) => {
                println!("❌ multipart 파싱 오류: {}", e);
                multipart_parse_error = true;
                // 파싱 오류가 발생해도 지금까지 읽은 데이터는 유지
                break;
            }
        }
    }
    
    println!("📊 최종 결과:");
    println!("  - video_path: '{}'", video_path);
    println!("  - video_name: '{}'", video_name);
    println!("  - multipart_parse_error: {}", multipart_parse_error);
    
    if video_path.is_empty() {
        println!("❌ video_path가 비어있음 - 업로드 실패");
        return JsonResponse(UploadVideoResponse { 
            success: false, 
            data: None,
            error: Some("비디오 ID가 제공되지 않았습니다.".to_string())
        });
    }
    
    // 파일이 실제로 존재하는지 확인
    if !std::path::Path::new(&video_path).exists() {
        println!("❌ 파일이 존재하지 않음: {}", video_path);
        return JsonResponse(UploadVideoResponse { 
            success: false, 
            data: None,
            error: Some("파일 저장에 실패했습니다.".to_string())
        });
    }
    
    println!("🚀 Video MCP 서버에 add_video 도구 호출 시작...");
    
    // Video MCP 서버에 비디오 추가 요청
    let guard = state.mcp.lock().await;
    let args = serde_json::json!({
        "video_path": video_path.clone(),
        "video_name": if video_name.is_empty() { None } else { Some(video_name.clone()) }
    });
    
    println!("📤 MCP 서버로 전송할 데이터: {:?}", args);
    
    match guard.call_video_tool("add_video", args).await {
        Ok(result) => {
            println!("✅ Video MCP 서버 응답: {:?}", result);
            JsonResponse(UploadVideoResponse { 
                success: true, 
                data: Some(serde_json::json!({
                    "message": "비디오 업로드 및 분석 완료",
                    "video_path": video_path,
                    "video_name": video_name
                })),
                error: None
            })
        }
        Err(e) => {
            eprintln!("❌ Video MCP 서버 오류: {}", e);
            JsonResponse(UploadVideoResponse { 
                success: false, 
                data: None,
                error: Some(format!("Video MCP 서버 오류: {}", e))
            })
        }
    }
}

// 트렌딩 분석 함수 (아직 구현되지 않음)
async fn trending_analysis(State(_state): State<AppState>, Json(payload): Json<TrendingAnalysisRequest>) -> JsonResponse<TrendingAnalysisResponse> {
    println!("📊 트렌딩 분석 요청 받음: {:?}", payload);  // 로그 출력
    
    let region = payload.region.unwrap_or_else(|| "KR".to_string());  // 지역 (없으면 한국)
    let max_results = payload.max_results.unwrap_or(10);  // 최대 결과 수 (없으면 10)
    
    // YouTube MCP 서버에 트렌딩 분석 요청 (실제로는 구현 필요)
    JsonResponse(TrendingAnalysisResponse { 
        success: true, 
        data: Some(serde_json::json!({
            "message": "트렌딩 분석 기능은 아직 구현되지 않았습니다",  // 임시 메시지
            "region": region,
            "max_results": max_results
        })),
        error: None
    })
}

// 메인 함수 (서버 시작점)
#[tokio::main]  // 비동기 메인 함수
async fn main() {
    println!("🚀 백엔드(HTTP for UI) + HTTP 기반 MCP 클라이언트 시작 중...");  // 시작 로그

    let client = MCPHTTPClient::new();  // MCP 클라이언트 생성
    
    // 백그라운드에서 MCP 서버 헬스 체크 (5초 후에 실행)
    let health_client = client.clone();  // 클라이언트 복사
    tokio::spawn(async move {  // 백그라운드 태스크 시작
        tokio::time::sleep(tokio::time::Duration::from_secs(5)).await;  // 5초 대기
        if let Err(e) = health_client.health_check().await {  // 헬스 체크 실행
            eprintln!("⚠️ MCP 서버 헬스 체크 실패: {}", e);  // 에러 출력
        }
    });

    let state = AppState {  // 앱 상태 생성
        mcp: Arc::new(Mutex::new(client)),  // MCP 클라이언트를 상태에 저장
    };

    // CORS 설정 (웹 브라우저에서 다른 도메인 접근 허용)
    let cors = tower_http::cors::CorsLayer::new()
        .allow_methods([Method::GET, Method::POST])  // GET, POST 메서드 허용
        .allow_origin(tower_http::cors::Any);        // 모든 도메인 허용

    // 라우터 설정 (URL 경로와 함수 연결)
    let app = Router::new()
        .route("/health", get(|| async { "ok" }))                    // 헬스 체크 엔드포인트
        .route("/", get(|| async { Html(include_str!("../static/index.html")) }))  // 메인 페이지
        .route("/static/app.js", get(|| async { Html(include_str!("../static/app.js")) }))  // JavaScript 파일
        .route("/static/style.css", get(|| async { Html(include_str!("../static/style.css")) }))  // CSS 파일
        .route("/api/youtube/search", post(youtube_search))          // YouTube 검색 API
        .route("/api/search-video", post(video_search))              // 비디오 검색 API (핵심!)
        .route("/api/channel-info", post(channel_info))              // 채널 정보 API
        .route("/api/channel/info", post(channel_info))              // 채널 정보 API (별칭)
        .route("/api/transcript", post(transcript_extraction))       // 자막 추출 API
        .route("/api/transcript-extraction", post(transcript_extraction))  // 자막 추출 API (별칭)
        .route("/api/save-single-video", post(save_video))           // 비디오 저장 API
        .route("/api/save-video", post(save_video))                  // 비디오 저장 API (별칭)
        .route("/api/search-similar", post(search_similar))          // 유사도 검색 API
        .route("/api/upload-video", post(upload_video))              // 비디오 업로드 API
        .route("/api/trending-analysis", post(trending_analysis))    // 트렌딩 분석 API
        .with_state(state)                                           // 상태 추가
        .layer(cors);                                                // CORS 설정 추가

    let listener = tokio::net::TcpListener::bind("0.0.0.0:8080").await.unwrap();  // 8080 포트에서 대기
    println!("✅ HTTP(UI) 서버가 8080에서 대기 중 (호스트 3000)");  // 로그 출력
    axum::serve(listener, app).await.unwrap();  // 서버 시작
} 