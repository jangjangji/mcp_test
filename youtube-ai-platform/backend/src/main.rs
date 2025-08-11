use actix_cors::Cors;
use actix_web::{web, App, HttpServer, HttpResponse, Result, middleware::Logger};
use actix_files::Files;
use actix_multipart::Multipart;
use futures::{TryStreamExt};
use serde::{Deserialize, Serialize};
use dotenv::dotenv;
use chrono::Utc;
use std::fs;
use std::path::Path;
use std::io::Write;
use reqwest;

// JSON 요청/응답 구조체들
#[derive(Serialize, Deserialize)]
struct SearchRequest {
    query: String,
}

#[derive(Serialize, Deserialize)]
struct VideoSearchRequest {
    query: String,
}

#[derive(Serialize, Deserialize)]
struct ChannelRequest {
    video_url: String,
}

#[derive(Serialize, Deserialize)]
struct SaveChannelRequest {
    channel_id: String,
}

#[derive(Serialize, Deserialize)]
struct TranscriptRequest {
    url: String,
}

#[derive(Serialize, Deserialize)]
struct SaveSingleVideoRequest {
    video_url: String,
}

#[derive(Serialize, Deserialize)]
struct ProgressRequest {
    channel_id: String,
}

// 비디오 업로드 및 검색 관련 구조체들
#[derive(Serialize, Deserialize)]
struct VideoUploadResponse {
    video_id: String,
    message: String,
}

#[derive(Serialize, Deserialize)]
struct VideoSearchResponse {
    video_id: String,
    video_path: String,
    timestamp: f64,
    similarity: f64,
}

#[derive(Serialize, Deserialize)]
struct VideoSearchResult {
    results: Vec<VideoSearchResponse>,
    query: String,
}

#[derive(Serialize, Deserialize)]
struct CompareChunkingRequest {
    video_url: String,
}

#[derive(Serialize, Deserialize)]
struct SaveSingleVideoSemanticRequest {
    video_url: String,
    chunk_method: String,
}

#[derive(Serialize, Deserialize)]
struct ApiResponse<T> {
    success: bool,
    data: Option<T>,
    error: Option<String>,
}

// MCP 클라이언트 구조체
struct MCPClient;

impl MCPClient {
    // HTTP로 YouTube MCP 서버와 통신
    async fn call_youtube_function(function_name: &str, args: serde_json::Value) -> Result<String, anyhow::Error> {
        let client = reqwest::Client::new();
        
        // YouTube MCP 서버 URL (환경 변수에서 가져오기)
        let url = std::env::var("YOUTUBE_MCP_URL")
            .unwrap_or_else(|_| "http://localhost:8001".to_string());
        
        let response = client.post(&format!("{}/{}", url, function_name))
            .json(&args)
            .send()
            .await?;
            
        if response.status().is_success() {
            let result = response.text().await?;
            Ok(result)
        } else {
            Err(anyhow::anyhow!("YouTube MCP 서버 오류: {}", response.status()))
        }
    }
    
    // HTTP로 Video MCP 서버와 통신
    async fn call_video_function(function_name: &str, args: serde_json::Value) -> Result<String, anyhow::Error> {
        let client = reqwest::Client::new();
        
        // Video MCP 서버 URL (환경 변수에서 가져오기)
        let url = std::env::var("VIDEO_MCP_URL")
            .unwrap_or_else(|_| "http://localhost:8002".to_string());
        
        let response = client.post(&format!("{}/{}", url, function_name))
            .json(&args)
            .send()
            .await?;
            
        if response.status().is_success() {
            let result = response.text().await?;
            Ok(result)
        } else {
            Err(anyhow::anyhow!("Video MCP 서버 오류: {}", response.status()))
        }
    }
}

// API 엔드포인트 함수들
async fn search_similar_video(req: web::Json<SearchRequest>) -> Result<HttpResponse> {
    let args = serde_json::json!({
        "query": req.query
    });
    
    match MCPClient::call_youtube_function("youtube_search", args).await {
        Ok(result) => {
            // MCP 툴 결과 파싱 (JSON 문자열을 파싱)
            match serde_json::from_str::<serde_json::Value>(&result) {
                Ok(data) => {
                    // MCP 툴 결과에서 실제 데이터 추출
                    let result_data = if let Some(result_value) = data.get("result") {
                        if let Some(content) = result_value.get("content") {
                            if let Some(first_content) = content.as_array().and_then(|arr| arr.first()) {
                                if let Some(text) = first_content.get("text") {
                                    // JSON 문자열을 파싱하여 실제 데이터 추출
                                    match serde_json::from_str::<serde_json::Value>(text.as_str().unwrap_or("")) {
                                        Ok(parsed_data) => parsed_data,
                                        Err(_) => result_value.clone()
                                    }
                                } else {
                                    result_value.clone()
                                }
                            } else {
                                result_value.clone()
                            }
                        } else {
                            result_value.clone()
                        }
                    } else {
                        data
                    };
                    
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(result_data),
                        error: None,
                    }))
                },
                Err(e) => {
                    println!("JSON 파싱 오류: {}", e);
                    Ok(HttpResponse::InternalServerError().json(ApiResponse::<()> {
                        success: false,
                        data: None,
                        error: Some(format!("JSON 파싱 오류: {}", e)),
                    }))
                }
            }
        },
        Err(e) => {
            println!("MCP 함수 호출 오류: {}", e);
            Ok(HttpResponse::InternalServerError().json(ApiResponse::<()> {
                success: false,
                data: None,
                error: Some(e.to_string()),
            }))
        }
    }
}

async fn search_youtube_videos(req: web::Json<VideoSearchRequest>) -> Result<HttpResponse> {
    let args = serde_json::json!({
        "query": req.query
    });
    
    match MCPClient::call_youtube_function("youtube_search", args).await {
        Ok(result) => {
            match serde_json::from_str::<serde_json::Value>(&result) {
                Ok(data) => {
                    // MCP 클라이언트에서 반환하는 데이터에서 "result" 필드를 추출
                    let result_data = if let Some(result_value) = data.get("result") {
                        // result가 문자열인 경우 JSON으로 파싱
                        if let serde_json::Value::String(s) = result_value {
                            match serde_json::from_str::<serde_json::Value>(s) {
                                Ok(parsed) => parsed,
                                Err(_) => result_value.clone()
                            }
                        } else {
                            result_value.clone()
                        }
                    } else {
                        data
                    };
                    
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(result_data),
                        error: None,
                    }))
                },
                Err(e) => {
                    println!("JSON 파싱 오류: {}", e);
                    Ok(HttpResponse::InternalServerError().json(ApiResponse::<()> {
                        success: false,
                        data: None,
                        error: Some(format!("JSON 파싱 오류: {}", e)),
                    }))
                }
            }
        },
        Err(e) => {
            println!("MCP 함수 호출 오류: {}", e);
            Ok(HttpResponse::InternalServerError().json(ApiResponse::<()> {
                success: false,
                data: None,
                error: Some(e.to_string()),
            }))
        }
    }
}

async fn get_channel_info(req: web::Json<ChannelRequest>) -> Result<HttpResponse> {
    let args = serde_json::json!({
        "video_url": req.video_url
    });
    
    match MCPClient::call_youtube_function("get_channel_info", args).await {
        Ok(result) => {
            match serde_json::from_str::<serde_json::Value>(&result) {
                Ok(data) => {
                    // MCP 클라이언트에서 반환하는 데이터에서 "result" 필드를 추출
                    let result_data = if let Some(result_value) = data.get("result") {
                        result_value.clone()
                    } else {
                        data
                    };
                    
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(result_data),
                        error: None,
                    }))
                },
                Err(e) => {
                    println!("JSON 파싱 오류: {}", e);
                    Ok(HttpResponse::InternalServerError().json(ApiResponse::<()> {
                        success: false,
                        data: None,
                        error: Some(format!("JSON 파싱 오류: {}", e)),
                    }))
                }
            }
        },
        Err(e) => {
            println!("MCP 함수 호출 오류: {}", e);
            Ok(HttpResponse::InternalServerError().json(ApiResponse::<()> {
                success: false,
                data: None,
                error: Some(e.to_string()),
            }))
        }
    }
}

async fn save_channel_embeddings(req: web::Json<SaveChannelRequest>) -> Result<HttpResponse> {
    let args = serde_json::json!({
        "channel_id": req.channel_id
    });
    
    match MCPClient::call_youtube_function("save_channel_youtube_embeddings", args).await {
        Ok(result) => {
            match serde_json::from_str::<serde_json::Value>(&result) {
                Ok(data) => {
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(data),
                        error: None,
                    }))
                },
                Err(_) => {
                    // 문자열로 반환된 경우
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(serde_json::json!({ "message": result })),
                        error: None,
                    }))
                }
            }
        },
        Err(e) => {
            println!("MCP 함수 호출 오류: {}", e);
            Ok(HttpResponse::InternalServerError().json(ApiResponse::<()> {
                success: false,
                data: None,
                error: Some(e.to_string()),
            }))
        }
    }
}

async fn save_channel_embeddings_force(req: web::Json<SaveChannelRequest>) -> Result<HttpResponse> {
    let args = serde_json::json!({
        "channel_id": req.channel_id,
        "force_update": true
    });
    
    match MCPClient::call_youtube_function("save_channel_youtube_embeddings", args).await {
        Ok(result) => {
            match serde_json::from_str::<serde_json::Value>(&result) {
                Ok(data) => {
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(data),
                        error: None,
                    }))
                },
                Err(_) => {
                    // 문자열로 반환된 경우
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(serde_json::json!({ "message": result })),
                        error: None,
                    }))
                }
            }
        },
        Err(e) => {
            println!("MCP 함수 호출 오류: {}", e);
            Ok(HttpResponse::InternalServerError().json(ApiResponse::<()> {
                success: false,
                data: None,
                error: Some(e.to_string()),
            }))
        }
    }
}

async fn get_youtube_transcript(req: web::Json<TranscriptRequest>) -> Result<HttpResponse> {
    let args = serde_json::json!({
        "url": req.url
    });
    
    match MCPClient::call_youtube_function("get_youtube_transcript", args).await {
        Ok(result) => {
            match serde_json::from_str::<serde_json::Value>(&result) {
                Ok(data) => {
                    // MCP 클라이언트에서 반환하는 데이터에서 "result" 필드를 추출
                    let result_data = if let Some(result_value) = data.get("result") {
                        result_value.clone()
                    } else {
                        data
                    };
                    
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(result_data),
                        error: None,
                    }))
                },
                Err(_) => {
                    // 문자열로 반환된 경우
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(serde_json::json!({ "transcript": result })),
                        error: None,
                    }))
                }
            }
        },
        Err(e) => {
            println!("MCP 함수 호출 오류: {}", e);
            Ok(HttpResponse::InternalServerError().json(ApiResponse::<()> {
                success: false,
                data: None,
                error: Some(e.to_string()),
            }))
        }
    }
}

async fn save_single_video_embedding(req: web::Json<SaveSingleVideoRequest>) -> Result<HttpResponse> {
    let args = serde_json::json!({
        "video_url": req.video_url
    });
    
    match MCPClient::call_video_function("save_single_video_embedding", args).await {
        Ok(result) => {
            match serde_json::from_str::<serde_json::Value>(&result) {
                Ok(data) => {
                    // MCP 클라이언트에서 반환하는 데이터에서 "result" 필드를 추출
                    let result_data = if let Some(result_value) = data.get("result") {
                        result_value.clone()
                    } else {
                        data
                    };
                    
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(result_data),
                        error: None,
                    }))
                },
                Err(_) => {
                    // 문자열로 반환된 경우
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(serde_json::json!({ "message": result })),
                        error: None,
                    }))
                }
            }
        },
        Err(e) => {
            println!("MCP 함수 호출 오류: {}", e);
            Ok(HttpResponse::InternalServerError().json(ApiResponse::<()> {
                success: false,
                data: None,
                error: Some(e.to_string()),
            }))
        }
    }
}

async fn save_single_video_semantic_embedding(req: web::Json<SaveSingleVideoSemanticRequest>) -> Result<HttpResponse> {
    let args = serde_json::json!({
        "video_url": req.video_url,
        "chunk_method": req.chunk_method
    });
    
    match MCPClient::call_video_function("save_single_video_semantic_embedding", args).await {
        Ok(result) => {
            match serde_json::from_str::<serde_json::Value>(&result) {
                Ok(data) => {
                    let result_data = if let Some(result_value) = data.get("result") {
                        result_value.clone()
                    } else {
                        data
                    };
                    
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(result_data),
                        error: None,
                    }))
                },
                Err(_) => {
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(serde_json::json!({ "message": result })),
                        error: None,
                    }))
                }
            }
        },
        Err(e) => {
            println!("MCP 함수 호출 오류: {}", e);
            Ok(HttpResponse::InternalServerError().json(ApiResponse::<()> {
                success: false,
                data: None,
                error: Some(e.to_string()),
            }))
        }
    }
}

async fn compare_chunking_methods(req: web::Json<CompareChunkingRequest>) -> Result<HttpResponse> {
    let args = serde_json::json!({
        "video_url": req.video_url
    });
    
    match MCPClient::call_video_function("compare_chunking_methods", args).await {
        Ok(result) => {
            match serde_json::from_str::<serde_json::Value>(&result) {
                Ok(data) => {
                    let result_data = if let Some(result_value) = data.get("result") {
                        result_value.clone()
                    } else {
                        data
                    };
                    
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(result_data),
                        error: None,
                    }))
                },
                Err(_) => {
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(serde_json::json!({ "message": result })),
                        error: None,
                    }))
                }
            }
        },
        Err(e) => {
            println!("MCP 함수 호출 오류: {}", e);
            Ok(HttpResponse::InternalServerError().json(ApiResponse::<()> {
                success: false,
                data: None,
                error: Some(e.to_string()),
            }))
        }
    }
}

// 비디오 업로드 API 엔드포인트
async fn upload_video(mut payload: Multipart) -> Result<HttpResponse> {
    let mut uploaded_file_path = String::new();
    let mut video_id = String::new();
    let mut original_filename = String::new();

    // 업로드 디렉토리 생성
    let upload_dir = Path::new("uploads");
    if !upload_dir.exists() {
        fs::create_dir_all(upload_dir)?;
    }

    while let Some(item) = payload.try_next().await? {
        if item.name() == "video" {
            // 파일 업로드 처리
            let filename = format!("{}.mp4", uuid::Uuid::new_v4());
            let filepath = upload_dir.join(&filename);
            
            let mut f = fs::File::create(&filepath)?;
            let mut buffer = Vec::new();
            
            // 파일 데이터 읽기
            let mut stream = item.into_stream();
            while let Some(chunk) = stream.try_next().await? {
                buffer.extend_from_slice(&chunk);
            }
            
            f.write_all(&buffer)?;
            uploaded_file_path = filepath.to_string_lossy().to_string();
            
        } else if item.name() == "video_id" {
            // 비디오 ID 처리
            let mut buffer = Vec::new();
            let mut stream = item.into_stream();
            while let Some(chunk) = stream.try_next().await? {
                buffer.extend_from_slice(&chunk);
            }
            video_id = String::from_utf8(buffer).map_err(|e| {
                actix_web::error::ErrorBadRequest(format!("Invalid UTF-8 in video_id: {}", e))
            })?;
        } else if item.name() == "original_filename" {
            // 원본 파일명 처리
            let mut buffer = Vec::new();
            let mut stream = item.into_stream();
            while let Some(chunk) = stream.try_next().await? {
                buffer.extend_from_slice(&chunk);
            }
            original_filename = String::from_utf8(buffer).map_err(|e| {
                actix_web::error::ErrorBadRequest(format!("Invalid UTF-8 in original_filename: {}", e))
            })?;
        }
    }

    if uploaded_file_path.is_empty() {
        return Ok(HttpResponse::BadRequest().json(ApiResponse::<()> {
            success: false,
            data: None,
            error: Some("비디오 파일이 업로드되지 않았습니다.".to_string()),
        }));
    }

    // video_id가 없으면 원본 파일명 사용
    if video_id.is_empty() {
        if !original_filename.is_empty() {
            // 원본 파일명에서 확장자 제거
            if let Some(dot_pos) = original_filename.rfind('.') {
                video_id = original_filename[..dot_pos].to_string();
            } else {
                video_id = original_filename;
            }
        } else {
            // 원본 파일명도 없으면 기본값 사용
            video_id = "uploaded_video".to_string();
        }
    }

    // 절대 경로로 변환
    let absolute_path = fs::canonicalize(&uploaded_file_path)?;
    let absolute_path_str = absolute_path.to_string_lossy().to_string();

    let args = serde_json::json!({
        "video_path": absolute_path_str,
        "video_id": video_id
    });
    
    match MCPClient::call_video_function("add_video_to_db", args).await {
        Ok(result) => {
            match serde_json::from_str::<serde_json::Value>(&result) {
                Ok(data) => {
                    let result_data = if let Some(result_value) = data.get("result") {
                        result_value.clone()
                    } else {
                        data
                    };
                    
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(result_data),
                        error: None,
                    }))
                },
                Err(_) => {
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(serde_json::json!({ "message": result })),
                        error: None,
                    }))
                }
            }
        },
        Err(e) => {
            println!("비디오 업로드 오류: {}", e);
            Ok(HttpResponse::InternalServerError().json(ApiResponse::<()> {
                success: false,
                data: None,
                error: Some(e.to_string()),
            }))
        }
    }
}

// YouTube 검색 API 엔드포인트
async fn search_youtube(req: web::Json<SearchRequest>) -> Result<HttpResponse> {
    let args = serde_json::json!({
        "query": req.query
    });
    
    match MCPClient::call_youtube_function("youtube_search", args).await {
        Ok(result) => {
            match serde_json::from_str::<serde_json::Value>(&result) {
                Ok(data) => {
                    // MCP 서버 응답에서 data 필드 추출
                    let result_data = if let Some(data_field) = data.get("data") {
                        data_field.clone()
                    } else {
                        data
                    };
                    
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(result_data),
                        error: None,
                    }))
                },
                Err(_) => {
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(serde_json::json!({ "message": result })),
                        error: None,
                    }))
                }
            }
        },
        Err(e) => {
            println!("YouTube 검색 오류: {}", e);
            Ok(HttpResponse::InternalServerError().json(ApiResponse::<()> {
                success: false,
                data: None,
                error: Some(e.to_string()),
            }))
        }
    }
}

// 트렌딩 분석 API 엔드포인트
async fn analyze_trending(req: web::Json<serde_json::Value>) -> Result<HttpResponse> {
    let args = serde_json::json!({
        "region": req.get("region").unwrap_or(&serde_json::Value::String("KR".to_string())),
        "category": req.get("category").unwrap_or(&serde_json::Value::String("all".to_string()))
    });
    
    match MCPClient::call_youtube_function("youtube_analyze_trending", args).await {
        Ok(result) => {
            match serde_json::from_str::<serde_json::Value>(&result) {
                Ok(data) => {
                    let result_data = if let Some(data_field) = data.get("data") {
                        data_field.clone()
                    } else {
                        data
                    };
                    
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(result_data),
                        error: None,
                    }))
                },
                Err(_) => {
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(serde_json::json!({ "message": result })),
                        error: None,
                    }))
                }
            }
        },
        Err(e) => {
            println!("트렌딩 분석 오류: {}", e);
            Ok(HttpResponse::InternalServerError().json(ApiResponse::<()> {
                success: false,
                data: None,
                error: Some(e.to_string()),
            }))
        }
    }
}

// 비디오 검색 API 엔드포인트
async fn search_video(req: web::Json<serde_json::Value>) -> Result<HttpResponse> {
    let args = serde_json::json!({
        "query": req["query"],
        "top_k": req["top_k"].as_u64().unwrap_or(5)
    });
    
    match MCPClient::call_video_function("search_video_in_db", args).await {
        Ok(result) => {
            println!("Python MCP 클라이언트 반환값: {}", result); // 디버깅 로그
            
            // Python MCP 클라이언트 반환값에서 JSON 부분만 추출
            let json_start = result.find('[');
            let json_end = result.rfind(']');
            
            if let (Some(start), Some(end)) = (json_start, json_end) {
                let json_str = &result[start..=end];
                println!("추출된 JSON 문자열: {}", json_str); // 디버깅 로그
                
                // 이스케이프된 문자열을 처리
                let unescaped_str = json_str.replace("\\\"", "\"").replace("\\\\", "\\");
                println!("이스케이프 해제된 문자열: {}", unescaped_str); // 디버깅 로그
                
                // JSON 문자열을 파싱
                match serde_json::from_str::<serde_json::Value>(&unescaped_str) {
                    Ok(data) => {
                        println!("성공적으로 파싱됨: {:?}", data); // 디버깅 로그
                        Ok(HttpResponse::Ok().json(ApiResponse {
                            success: true,
                            data: Some(data),
                            error: None,
                        }))
                    },
                    Err(e) => {
                        println!("JSON 파싱 오류: {}", e); // 디버깅 로그
                        // JSON 파싱 실패 시 빈 배열 반환
                        Ok(HttpResponse::Ok().json(ApiResponse {
                            success: true,
                            data: Some(serde_json::json!([])),
                            error: None,
                        }))
                    }
                }
            } else {
                println!("JSON 배열을 찾을 수 없음"); // 디버깅 로그
                // JSON 배열을 찾을 수 없는 경우 빈 배열 반환
                Ok(HttpResponse::Ok().json(ApiResponse {
                    success: true,
                    data: Some(serde_json::json!([])),
                    error: None,
                }))
            }
        },
        Err(e) => {
            println!("비디오 검색 오류: {}", e);
            Ok(HttpResponse::InternalServerError().json(ApiResponse::<()> {
                success: false,
                data: None,
                error: Some(e.to_string()),
            }))
        }
    }
}

// 비디오 삭제 API 엔드포인트
async fn delete_video(req: web::Json<serde_json::Value>) -> Result<HttpResponse> {
    let args = serde_json::json!({
        "video_id": req["video_id"]
    });
    
    match MCPClient::call_video_function("clear_video_from_db", args).await {
        Ok(result) => {
            match serde_json::from_str::<serde_json::Value>(&result) {
                Ok(data) => {
                    let result_data = if let Some(result_value) = data.get("result") {
                        result_value.clone()
                    } else {
                        data
                    };
                    
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(result_data),
                        error: None,
                    }))
                },
                Err(_) => {
                    Ok(HttpResponse::Ok().json(ApiResponse {
                        success: true,
                        data: Some(serde_json::json!({ "message": result })),
                        error: None,
                    }))
                }
            }
        },
        Err(e) => {
            println!("비디오 삭제 오류: {}", e);
            Ok(HttpResponse::InternalServerError().json(ApiResponse::<()> {
                success: false,
                data: None,
                error: Some(e.to_string()),
            }))
        }
    }
}

async fn health_check() -> Result<HttpResponse> {
    Ok(HttpResponse::Ok().json(serde_json::json!({
        "status": "healthy",
        "timestamp": Utc::now(),
        "version": "1.0.0"
    })))
}

async fn root() -> Result<HttpResponse> {
    Ok(HttpResponse::Ok()
        .content_type("text/html; charset=utf-8")
        .body(include_str!("../static/index.html")))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    dotenv().ok();
    env_logger::init();

    println!("🚀 YouTube Search API Server 시작 중...");
    println!("📍 서버 주소: http://127.0.0.1:8080");
    println!("🔧 MCP 서버와 연동 중...");

    HttpServer::new(|| {
        let cors = Cors::default()
            .allow_any_origin()
            .allow_any_method()
            .allow_any_header();

        App::new()
            .wrap(cors)
            .wrap(Logger::default())
            .service(Files::new("/static", "./static").show_files_listing())
            .route("/", web::get().to(root))
            .route("/health", web::get().to(health_check))
            .route("/api/youtube/search", web::post().to(search_youtube))
            .route("/api/analyze-trending", web::post().to(analyze_trending))
            .route("/api/search-similar", web::post().to(search_similar_video))
            .route("/api/search-youtube", web::post().to(search_youtube_videos))
            .route("/api/channel-info", web::post().to(get_channel_info))
            .route("/api/save-channel", web::post().to(save_channel_embeddings))
            .route("/api/save-channel-force", web::post().to(save_channel_embeddings_force))
            .route("/api/transcript", web::post().to(get_youtube_transcript))
            .route("/api/save-single-video", web::post().to(save_single_video_embedding))
            .route("/api/save-single-video-semantic", web::post().to(save_single_video_semantic_embedding))
            .route("/api/compare-chunking", web::post().to(compare_chunking_methods))
            .route("/api/analyze-trending", web::post().to(analyze_trending))
            // 비디오 업로드 및 검색 API 엔드포인트들
            .route("/api/upload-video", web::post().to(upload_video))
            .route("/api/search-video", web::post().to(search_video))
            .route("/api/delete-video", web::post().to(delete_video))
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
} 