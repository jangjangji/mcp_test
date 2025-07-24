use actix_cors::Cors;
use actix_web::{web, App, HttpServer, HttpResponse, Result, middleware::Logger};
use actix_files::Files;
use serde::{Deserialize, Serialize};
use dotenv::dotenv;
use chrono::Utc;
use std::process::Command;

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
struct ApiResponse<T> {
    success: bool,
    data: Option<T>,
    error: Option<String>,
}

// MCP 클라이언트 구조체
struct MCPClient;

impl MCPClient {
    // Python MCP 서버와 통신하는 함수
    async fn call_function(function_name: &str, args: serde_json::Value) -> Result<String, anyhow::Error> {
        // 가상환경의 Python 사용
        let output = Command::new("./venv/bin/python")
            .current_dir(".")  // 현재 디렉토리에서 실행
            .arg("my_mcp_client.py")
            .arg(function_name)
            .arg(serde_json::to_string(&args)?)
            .output()?;

        if output.status.success() {
            let result = String::from_utf8(output.stdout)?;
            Ok(result.trim().to_string())
        } else {
            let error = String::from_utf8(output.stderr)?;
            let stdout = String::from_utf8(output.stdout)?;
            println!("Python 실행 오류 - stderr: {}, stdout: {}", error, stdout);
            Err(anyhow::anyhow!("Python 함수 실행 오류: {}", error))
        }
    }
}

// API 엔드포인트 함수들
async fn search_similar_video(req: web::Json<SearchRequest>) -> Result<HttpResponse> {
    let args = serde_json::json!({
        "query": req.query
    });
    
    match MCPClient::call_function("search_similar_youtube_video", args).await {
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

async fn search_youtube_videos(req: web::Json<VideoSearchRequest>) -> Result<HttpResponse> {
    let args = serde_json::json!({
        "query": req.query
    });
    
    match MCPClient::call_function("search_youtube_videos", args).await {
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
    
    match MCPClient::call_function("get_channel_info", args).await {
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
    
    match MCPClient::call_function("save_channel_youtube_embeddings", args).await {
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
    
    match MCPClient::call_function("get_youtube_transcript", args).await {
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
            .route("/api/search-similar", web::post().to(search_similar_video))
            .route("/api/search-youtube", web::post().to(search_youtube_videos))
            .route("/api/channel-info", web::post().to(get_channel_info))
            .route("/api/save-channel", web::post().to(save_channel_embeddings))
            .route("/api/transcript", web::post().to(get_youtube_transcript))
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
} 