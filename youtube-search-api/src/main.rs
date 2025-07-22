// 필요한 외부 라이브러리들을 가져옵니다 (import)
// actix_cors: 웹 브라우저의 CORS 정책을 처리하는 라이브러리
// actix_web: 웹 서버를 만드는 라이브러리
// actix_files: 정적 파일(HTML, CSS, JS)을 제공하는 라이브러리
// serde: JSON 데이터를 Rust 구조체로 변환하는 라이브러리
// std::env: 환경 변수를 읽는 표준 라이브러리
// dotenv: .env 파일에서 환경 변수를 로드하는 라이브러리
// chrono: 날짜와 시간을 다루는 라이브러리
use actix_cors::Cors;
use actix_web::{web, App, HttpServer, HttpResponse, Result, middleware::Logger};
use actix_files::Files;
use serde::{Deserialize, Serialize};
use std::env;
use dotenv::dotenv;
use chrono::{DateTime, Utc};

// JSON 요청 데이터를 받기 위한 구조체들
// #[derive(Serialize, Deserialize)]: 이 구조체를 JSON으로 변환/역변환할 수 있게 해줍니다

// 유사도 검색 요청을 받는 구조체
#[derive(Serialize, Deserialize)]
struct SearchRequest {
    query: String,  // 검색어
}

// YouTube 검색 요청을 받는 구조체
#[derive(Serialize, Deserialize)]
struct VideoSearchRequest {
    query: String,  // 검색어
}

// 채널 정보 요청을 받는 구조체
#[derive(Serialize, Deserialize)]
struct ChannelRequest {
    video_url: String,  // YouTube 영상 URL
}

// 채널 저장 요청을 받는 구조체
#[derive(Serialize, Deserialize)]
struct SaveChannelRequest {
    channel_id: String,  // YouTube 채널 ID
}

// 자막 요청을 받는 구조체
#[derive(Serialize, Deserialize)]
struct TranscriptRequest {
    url: String,  // YouTube 영상 URL
}

// YouTube 영상 정보를 담는 구조체
#[derive(Serialize, Deserialize)]
struct VideoInfo {
    title: String,           // 영상 제목
    published_date: String,  // 업로드 날짜
    channel_name: String,    // 채널명
    channel_id: String,      // 채널 ID
    thumbnail_url: String,   // 썸네일 이미지 URL
    view_count: Option<i64>, // 조회수 (없을 수도 있음)
    like_count: Option<i64>, // 좋아요 수 (없을 수도 있음)
    url: String,             // 영상 URL
}

// 채널 정보를 담는 구조체
#[derive(Serialize, Deserialize)]
struct ChannelInfo {
    channel_id: String,           // 채널 ID
    channel_name: String,         // 채널명
    recent_videos: Vec<VideoInfo>, // 최근 영상들 목록
}

// 검색 결과를 담는 구조체
#[derive(Serialize, Deserialize)]
struct SearchResponse {
    video_id: Option<String>,    // 비디오 ID (없을 수도 있음)
    url: Option<String>,         // 비디오 URL (없을 수도 있음)
    chunk_index: Option<i32>,    // 자막 청크 인덱스 (없을 수도 있음)
    chunk_text: Option<String>,  // 자막 텍스트 (없을 수도 있음)
    score: Option<f64>,          // 유사도 점수 (없을 수도 있음)
    error: Option<String>,       // 오류 메시지 (없을 수도 있음)
}

// 서버 상태 확인 응답을 담는 구조체
#[derive(Serialize, Deserialize)]
struct HealthResponse {
    status: String,              // 서버 상태 ("healthy" 등)
    timestamp: DateTime<Utc>,    // 현재 시간
    version: String,             // 서버 버전
}

// 오류 응답을 담는 구조체
#[derive(Serialize, Deserialize)]
struct ErrorResponse {
    error: String,   // 오류 타입
    message: String, // 오류 메시지
}

// 자막 응답을 담는 구조체
#[derive(Serialize, Deserialize)]
struct TranscriptResponse {
    transcript: String,      // 자막 내용
    error: Option<String>,   // 오류 메시지 (없을 수도 있음)
}

// 채널 저장 응답을 담는 구조체
#[derive(Serialize, Deserialize)]
struct SaveChannelResponse {
    message: String,         // 성공 메시지
    error: Option<String>,   // 오류 메시지 (없을 수도 있음)
}

// 유사도 검색 API 엔드포인트 함수
// async fn: 비동기 함수 (다른 작업을 기다리는 동안 다른 작업을 할 수 있음)
// web::Json<SearchRequest>: JSON 형태로 SearchRequest 구조체를 받음
// Result<HttpResponse>: 성공하면 HttpResponse, 실패하면 오류를 반환
async fn search_similar_video(req: web::Json<SearchRequest>) -> Result<HttpResponse> {
    // .env 파일에서 환경 변수를 로드
    dotenv().ok();
    
    // OpenAI API 키를 환경 변수에서 가져오기
    let openai_api_key = match env::var("OPENAI_API_KEY") {
        Ok(key) => key,  // 성공하면 API 키 반환
        Err(_) => {
            // 실패하면 오류 응답 반환
            return Ok(HttpResponse::InternalServerError().json(ErrorResponse {
                error: "Configuration Error".to_string(),
                message: "OPENAI_API_KEY not set".to_string(),
            }))
        }
    };
    
    // Supabase URL을 환경 변수에서 가져오기
    let supabase_url = match env::var("SUPABASE_URL") {
        Ok(url) => url,
        Err(_) => {
            return Ok(HttpResponse::InternalServerError().json(ErrorResponse {
                error: "Configuration Error".to_string(),
                message: "SUPABASE_URL not set".to_string(),
            }))
        }
    };
    
    // Supabase API 키를 환경 변수에서 가져오기
    let supabase_key = match env::var("SUPABASE_KEY") {
        Ok(key) => key,
        Err(_) => {
            return Ok(HttpResponse::InternalServerError().json(ErrorResponse {
                error: "Configuration Error".to_string(),
                message: "SUPABASE_KEY not set".to_string(),
            }))
        }
    };
    
    // 1단계: OpenAI API를 사용해서 검색어를 벡터(임베딩)로 변환
    let embedding = match create_embedding(&req.query, &openai_api_key).await {
        Ok(emb) => emb,  // 성공하면 임베딩 벡터 반환
        Err(e) => {
            // 실패하면 오류 응답 반환
            return Ok(HttpResponse::InternalServerError().json(ErrorResponse {
                error: "Embedding Error".to_string(),
                message: e.to_string(),
            }))
        }
    };
    
    // 2단계: Supabase에서 유사한 비디오 검색
    let result = match search_supabase(&embedding, &supabase_url, &supabase_key).await {
        Ok(res) => res,  // 성공하면 검색 결과 반환
        Err(e) => {
            // 실패하면 오류 응답 반환
            return Ok(HttpResponse::InternalServerError().json(ErrorResponse {
                error: "Database Error".to_string(),
                message: e.to_string(),
            }))
        }
    };
    
    // 성공적으로 결과를 JSON 형태로 반환
    Ok(HttpResponse::Ok().json(result))
}

// YouTube 검색 API 엔드포인트 함수
async fn search_youtube_videos(req: web::Json<VideoSearchRequest>) -> Result<HttpResponse> {
    dotenv().ok();
    
    // YouTube API 키를 환경 변수에서 가져오기
    let youtube_api_key = match env::var("YOUTUBE_API_KEY") {
        Ok(key) => key,
        Err(_) => {
            return Ok(HttpResponse::InternalServerError().json(ErrorResponse {
                error: "Configuration Error".to_string(),
                message: "YOUTUBE_API_KEY not set".to_string(),
            }))
        }
    };
    
    // YouTube API를 사용해서 비디오 검색
    let videos = match search_youtube_api(&req.query, &youtube_api_key).await {
        Ok(vids) => vids,  // 성공하면 비디오 목록 반환
        Err(e) => {
            // 실패하면 오류 응답 반환
            return Ok(HttpResponse::InternalServerError().json(ErrorResponse {
                error: "YouTube API Error".to_string(),
                message: e.to_string(),
            }))
        }
    };
    
    // 성공적으로 비디오 목록을 JSON 형태로 반환
    Ok(HttpResponse::Ok().json(videos))
}

// 채널 정보 가져오기 API 엔드포인트 함수
async fn get_channel_info(req: web::Json<ChannelRequest>) -> Result<HttpResponse> {
    dotenv().ok();
    
    // YouTube API 키를 환경 변수에서 가져오기
    let youtube_api_key = match env::var("YOUTUBE_API_KEY") {
        Ok(key) => key,
        Err(_) => {
            return Ok(HttpResponse::InternalServerError().json(ErrorResponse {
                error: "Configuration Error".to_string(),
                message: "YOUTUBE_API_KEY not set".to_string(),
            }))
        }
    };
    
    // YouTube API를 사용해서 채널 정보 가져오기
    let channel_info = match fetch_channel_info(&req.video_url, &youtube_api_key).await {
        Ok(info) => info,  // 성공하면 채널 정보 반환
        Err(e) => {
            // 실패하면 오류 응답 반환
            return Ok(HttpResponse::InternalServerError().json(ErrorResponse {
                error: "Channel Info Error".to_string(),
                message: e.to_string(),
            }))
        }
    };
    
    // 성공적으로 채널 정보를 JSON 형태로 반환
    Ok(HttpResponse::Ok().json(channel_info))
}

// 채널 임베딩 저장 API 엔드포인트 함수
async fn save_channel_embeddings(req: web::Json<SaveChannelRequest>) -> Result<HttpResponse> {
    dotenv().ok();
    
    // 필요한 API 키들을 환경 변수에서 가져오기
    let youtube_api_key = match env::var("YOUTUBE_API_KEY") {
        Ok(key) => key,
        Err(_) => {
            return Ok(HttpResponse::InternalServerError().json(ErrorResponse {
                error: "Configuration Error".to_string(),
                message: "YOUTUBE_API_KEY not set".to_string(),
            }))
        }
    };
    
    let openai_api_key = match env::var("OPENAI_API_KEY") {
        Ok(key) => key,
        Err(_) => {
            return Ok(HttpResponse::InternalServerError().json(ErrorResponse {
                error: "Configuration Error".to_string(),
                message: "OPENAI_API_KEY not set".to_string(),
            }))
        }
    };
    
    let supabase_url = match env::var("SUPABASE_URL") {
        Ok(url) => url,
        Err(_) => {
            return Ok(HttpResponse::InternalServerError().json(ErrorResponse {
                error: "Configuration Error".to_string(),
                message: "SUPABASE_URL not set".to_string(),
            }))
        }
    };
    
    let supabase_key = match env::var("SUPABASE_KEY") {
        Ok(key) => key,
        Err(_) => {
            return Ok(HttpResponse::InternalServerError().json(ErrorResponse {
                error: "Configuration Error".to_string(),
                message: "SUPABASE_KEY not set".to_string(),
            }))
        }
    };
    
    // 채널 임베딩 저장 실행
    let result = match save_channel_embeddings_impl(&req.channel_id, &youtube_api_key, &openai_api_key, &supabase_url, &supabase_key).await {
        Ok(msg) => SaveChannelResponse { message: msg, error: None },  // 성공
        Err(e) => SaveChannelResponse { message: "".to_string(), error: Some(e.to_string()) },  // 실패
    };
    
    // 결과를 JSON 형태로 반환
    Ok(HttpResponse::Ok().json(result))
}

// YouTube 자막 가져오기 API 엔드포인트 함수
async fn get_youtube_transcript(req: web::Json<TranscriptRequest>) -> Result<HttpResponse> {
    // YouTube 자막 가져오기
    let transcript = match fetch_transcript(&req.url).await {
        Ok(trans) => trans,  // 성공하면 자막 반환
        Err(e) => {
            // 실패하면 오류 응답 반환
            return Ok(HttpResponse::InternalServerError().json(TranscriptResponse {
                transcript: "".to_string(),
                error: Some(e.to_string()),
            }))
        }
    };
    
    // 성공적으로 자막을 JSON 형태로 반환
    Ok(HttpResponse::Ok().json(TranscriptResponse {
        transcript,
        error: None,
    }))
}

// OpenAI API를 사용해서 텍스트를 벡터(임베딩)로 변환하는 함수
// &str: 문자열 참조 (소유권을 빌려옴)
// anyhow::Error: 오류 타입
async fn create_embedding(query: &str, api_key: &str) -> Result<Vec<f64>, anyhow::Error> {
    // HTTP 클라이언트 생성
    let client = reqwest::Client::new();
    
    // OpenAI API에 보낼 요청 데이터 생성
    let request_body = serde_json::json!({
        "input": query,
        "model": "text-embedding-3-small"  // OpenAI의 임베딩 모델
    });
    
    // OpenAI API에 POST 요청 보내기
    let response = client
        .post("https://api.openai.com/v1/embeddings")
        .header("Authorization", format!("Bearer {}", api_key))  // API 키를 헤더에 추가
        .header("Content-Type", "application/json")
        .json(&request_body)  // JSON 데이터를 요청 본문에 추가
        .send()
        .await?;  // 비동기 요청 실행
    
    // 응답 상태 코드 확인
    if !response.status().is_success() {
        return Err(anyhow::anyhow!("OpenAI API error: {}", response.status()));
    }
    
    // 응답을 JSON으로 파싱
    let response_json: serde_json::Value = response.json().await?;
    
    // 응답에서 임베딩 벡터 추출
    let embedding = response_json["data"][0]["embedding"]
        .as_array()  // 배열로 변환
        .ok_or_else(|| anyhow::anyhow!("Failed to parse embedding"))?  // 실패하면 오류
        .iter()  // 배열의 각 요소를 순회
        .map(|v| v.as_f64().unwrap_or(0.0))  // 각 요소를 f64로 변환 (실패하면 0.0)
        .collect();  // Vec<f64>로 수집
    
    Ok(embedding)  // 임베딩 벡터 반환
}

// Supabase에서 유사한 비디오를 검색하는 함수
async fn search_supabase(
    embedding: &[f64],  // 임베딩 벡터 참조
    supabase_url: &str, 
    supabase_key: &str
) -> Result<SearchResponse, anyhow::Error> {
    let client = reqwest::Client::new();
    
    // Supabase에 보낼 요청 데이터 생성
    let request_body = serde_json::json!({
        "input_vector": embedding
    });
    
    // Supabase RPC 함수 호출
    let response = client
        .post(format!("{}/rest/v1/rpc/match_youtube_video", supabase_url))
        .header("apikey", supabase_key)
        .header("Authorization", format!("Bearer {}", supabase_key))
        .header("Content-Type", "application/json")
        .json(&request_body)
        .send()
        .await?;
    
    // 응답이 성공인지 확인
    if response.status().is_success() {
        // 응답을 JSON 배열로 파싱
        let result: Vec<serde_json::Value> = response.json().await?;
        
        // 첫 번째 결과가 있는지 확인
        if let Some(first_result) = result.first() {
            // 검색 결과를 SearchResponse 구조체로 변환
            Ok(SearchResponse {
                video_id: first_result["video_id"].as_str().map(String::from),
                url: first_result["url"].as_str().map(String::from),
                chunk_index: first_result["chunk_index"].as_i64().map(|v| v as i32),
                chunk_text: first_result["chunk_text"].as_str().map(String::from),
                score: first_result["score"].as_f64(),
                error: None,
            })
        } else {
            // 결과가 없으면 빈 응답 반환
            Ok(SearchResponse {
                video_id: None,
                url: None,
                chunk_index: None,
                chunk_text: None,
                score: None,
                error: Some("No similar video found.".to_string()),
            })
        }
    } else {
        // API 오류 발생
        Err(anyhow::anyhow!("Supabase API error: {}", response.status()))
    }
}

// YouTube API를 사용해서 비디오를 검색하는 함수
async fn search_youtube_api(query: &str, api_key: &str) -> Result<Vec<VideoInfo>, anyhow::Error> {
    let client = reqwest::Client::new();
    
    // YouTube 검색 API URL 생성
    let search_url = format!(
        "https://www.googleapis.com/youtube/v3/search?part=snippet&q={}&type=video&maxResults=20&key={}",
        urlencoding::encode(query),  // 검색어를 URL 인코딩
        api_key
    );
    
    // YouTube 검색 API 호출
    let response = client.get(&search_url).send().await?;
    
    // 응답 상태 확인
    if !response.status().is_success() {
        return Err(anyhow::anyhow!("YouTube API error: {}", response.status()));
    }
    
    // 검색 결과를 JSON으로 파싱
    let search_data: serde_json::Value = response.json().await?;
    
    // 검색 결과에서 비디오 ID들 추출
    let video_ids: Vec<String> = search_data["items"]
        .as_array()  // 배열로 변환
        .unwrap_or(&vec![])  // 실패하면 빈 배열
        .iter()  // 배열의 각 요소를 순회
        .filter_map(|item| {
            item["id"]["videoId"].as_str().map(String::from)  // videoId를 문자열로 변환
        })
        .collect();  // Vec<String>으로 수집
    
    // 비디오 ID가 없으면 빈 배열 반환
    if video_ids.is_empty() {
        return Ok(vec![]);
    }
    
    // 비디오 상세 정보를 가져오는 API URL 생성
    let details_url = format!(
        "https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={}&key={}",
        video_ids.join(","),  // 비디오 ID들을 쉼표로 구분
        api_key
    );
    
    // 비디오 상세 정보 API 호출
    let details_response = client.get(&details_url).send().await?;
    
    // 응답 상태 확인
    if !details_response.status().is_success() {
        return Err(anyhow::anyhow!("YouTube API details error: {}", details_response.status()));
    }
    
    // 상세 정보를 JSON으로 파싱
    let details_data: serde_json::Value = details_response.json().await?;
    
    // 각 비디오 정보를 VideoInfo 구조체로 변환
    let videos: Vec<VideoInfo> = details_data["items"]
        .as_array()
        .unwrap_or(&vec![])
        .iter()
        .map(|item| {
            let snippet = &item["snippet"];  // 비디오 기본 정보
            let statistics = &item["statistics"];  // 통계 정보
            let thumbnails = &snippet["thumbnails"];  // 썸네일 정보
            let high_thumbnail = &thumbnails["high"];  // 고화질 썸네일
            
            // VideoInfo 구조체 생성
            VideoInfo {
                title: snippet["title"].as_str().unwrap_or("N/A").to_string(),
                published_date: snippet["publishedAt"].as_str().unwrap_or("").to_string(),
                channel_name: snippet["channelTitle"].as_str().unwrap_or("N/A").to_string(),
                channel_id: snippet["channelId"].as_str().unwrap_or("").to_string(),
                thumbnail_url: high_thumbnail["url"].as_str().unwrap_or("").to_string(),
                view_count: statistics["viewCount"].as_str().and_then(|v| v.parse::<i64>().ok()),
                like_count: statistics["likeCount"].as_str().and_then(|v| v.parse::<i64>().ok()),
                url: format!("https://www.youtube.com/watch?v={}", item["id"].as_str().unwrap_or("")),
            }
        })
        .collect();
    
    Ok(videos)  // 비디오 목록 반환
}

// YouTube 영상 URL에서 채널 정보를 가져오는 함수
async fn fetch_channel_info(video_url: &str, api_key: &str) -> Result<ChannelInfo, anyhow::Error> {
    // URL에서 비디오 ID 추출
    let video_id = extract_video_id(video_url)?;
    
    let client = reqwest::Client::new();
    
    // 비디오 상세 정보를 가져와서 채널 ID 찾기
    let video_url = format!(
        "https://www.googleapis.com/youtube/v3/videos?part=snippet&id={}&key={}",
        video_id, api_key
    );
    
    let response = client.get(&video_url).send().await?;
    
    if !response.status().is_success() {
        return Err(anyhow::anyhow!("YouTube API error: {}", response.status()));
    }
    
    let data: serde_json::Value = response.json().await?;
    
    // 응답에서 채널 ID와 채널명 추출
    let channel_id = data["items"][0]["snippet"]["channelId"]
        .as_str()
        .ok_or_else(|| anyhow::anyhow!("Channel ID not found"))?;
    
    let channel_name = data["items"][0]["snippet"]["channelTitle"]
        .as_str()
        .unwrap_or("Unknown Channel");
    
    // 채널의 최근 영상들 가져오기
    let recent_videos = fetch_recent_videos(channel_id, api_key).await?;
    
    // ChannelInfo 구조체 생성 및 반환
    Ok(ChannelInfo {
        channel_id: channel_id.to_string(),
        channel_name: channel_name.to_string(),
        recent_videos,
    })
}

// 채널의 최근 영상들을 가져오는 함수
async fn fetch_recent_videos(channel_id: &str, api_key: &str) -> Result<Vec<VideoInfo>, anyhow::Error> {
    let client = reqwest::Client::new();
    
    // 채널의 최근 영상들을 검색하는 API URL
    let url = format!(
        "https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={}&order=date&type=video&maxResults=5&key={}",
        channel_id, api_key
    );
    
    let response = client.get(&url).send().await?;
    
    if !response.status().is_success() {
        return Err(anyhow::anyhow!("YouTube API error: {}", response.status()));
    }
    
    let data: serde_json::Value = response.json().await?;
    
    // 검색 결과에서 비디오 ID들 추출
    let video_ids: Vec<String> = data["items"]
        .as_array()
        .unwrap_or(&vec![])
        .iter()
        .filter_map(|item| {
            item["id"]["videoId"].as_str().map(String::from)
        })
        .collect();
    
    if video_ids.is_empty() {
        return Ok(vec![]);
    }
    
    // 비디오 상세 정보 가져오기
    let details_url = format!(
        "https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={}&key={}",
        video_ids.join(","),
        api_key
    );
    
    let details_response = client.get(&details_url).send().await?;
    
    if !details_response.status().is_success() {
        return Err(anyhow::anyhow!("YouTube API details error: {}", details_response.status()));
    }
    
    let details_data: serde_json::Value = details_response.json().await?;
    
    // 각 비디오 정보를 VideoInfo 구조체로 변환
    let videos: Vec<VideoInfo> = details_data["items"]
        .as_array()
        .unwrap_or(&vec![])
        .iter()
        .map(|item| {
            let snippet = &item["snippet"];
            let statistics = &item["statistics"];
            let thumbnails = &snippet["thumbnails"];
            let high_thumbnail = &thumbnails["high"];
            
            VideoInfo {
                title: snippet["title"].as_str().unwrap_or("N/A").to_string(),
                published_date: snippet["publishedAt"].as_str().unwrap_or("").to_string(),
                channel_name: snippet["channelTitle"].as_str().unwrap_or("N/A").to_string(),
                channel_id: snippet["channelId"].as_str().unwrap_or("").to_string(),
                thumbnail_url: high_thumbnail["url"].as_str().unwrap_or("").to_string(),
                view_count: statistics["viewCount"].as_str().and_then(|v| v.parse::<i64>().ok()),
                like_count: statistics["likeCount"].as_str().and_then(|v| v.parse::<i64>().ok()),
                url: format!("https://www.youtube.com/watch?v={}", item["id"].as_str().unwrap_or("")),
            }
        })
        .collect();
    
    Ok(videos)
}

// YouTube URL에서 비디오 ID를 추출하는 함수
fn extract_video_id(url: &str) -> Result<String, anyhow::Error> {
    // 정규표현식을 사용해서 YouTube URL에서 비디오 ID 추출
    let re = regex::Regex::new(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*")?;
    let captures = re.captures(url)
        .ok_or_else(|| anyhow::anyhow!("Invalid YouTube URL"))?;
    
    Ok(captures[1].to_string())  // 첫 번째 그룹(비디오 ID) 반환
}

// YouTube 자막을 가져오는 함수 (현재는 간단한 구현)
async fn fetch_transcript(url: &str) -> Result<String, anyhow::Error> {
    let video_id = extract_video_id(url)?;
    
    // 실제 구현에서는 YouTube 자막 API를 사용해야 함
    // 현재는 간단한 플레이스홀더 반환
    Ok(format!("Transcript for video {} would be fetched here", video_id))
}

// 채널의 모든 영상 자막을 임베딩하여 저장하는 함수 (현재는 간단한 구현)
async fn save_channel_embeddings_impl(
    channel_id: &str,
    youtube_api_key: &str,
    openai_api_key: &str,
    supabase_url: &str,
    supabase_key: &str,
) -> Result<String, anyhow::Error> {
    // 실제 구현에서는:
    // 1. 채널의 영상들을 가져오기
    // 2. 각 영상의 자막 가져오기
    // 3. 자막을 청크로 나누기
    // 4. 각 청크를 임베딩으로 변환
    // 5. Supabase에 저장
    
    // 현재는 간단한 플레이스홀더 반환
    Ok(format!("Channel {} embeddings would be saved here", channel_id))
}

// 서버 상태 확인 API 엔드포인트
async fn health_check() -> Result<HttpResponse> {
    Ok(HttpResponse::Ok().json(HealthResponse {
        status: "healthy".to_string(),
        timestamp: Utc::now(),  // 현재 UTC 시간
        version: env!("CARGO_PKG_VERSION").to_string(),  // Cargo.toml의 버전
    }))
}

// 루트 경로(/)에 접근했을 때 HTML 페이지를 제공하는 함수
async fn root() -> Result<HttpResponse> {
    Ok(HttpResponse::Ok()
        .content_type("text/html; charset=utf-8")  // HTML 타입 설정
        .body(include_str!("../static/index.html")))  // HTML 파일 내용을 바이너리에 포함
}

// 메인 함수 - 서버를 시작하는 함수
#[actix_web::main]  // actix_web의 비동기 런타임을 사용
async fn main() -> std::io::Result<()> {
    // 로그 시스템 초기화
    env_logger::init();
    
    // 서버 시작 메시지 출력
    println!("Starting YouTube Search API server...");
    println!("Server running at http://127.0.0.1:8080");
    println!("Health check: http://127.0.0.1:8080/health");
    println!("Search API: http://127.0.0.1:8080/api/search");
    
    // HTTP 서버 생성 및 설정
    HttpServer::new(|| {
        // CORS 설정 (브라우저의 보안 정책)
        let cors = Cors::default()
            .allow_any_origin()    // 모든 출처 허용
            .allow_any_method()    // 모든 HTTP 메서드 허용
            .allow_any_header();   // 모든 헤더 허용
        
        // 웹 애플리케이션 설정
        App::new()
            .wrap(cors)  // CORS 미들웨어 추가
            .wrap(Logger::default())  // 로깅 미들웨어 추가
            .service(Files::new("/static", "./static").show_files_listing())  // 정적 파일 제공
            .service(web::resource("/").route(web::get().to(root)))  // 루트 경로
            .service(web::resource("/health").route(web::get().to(health_check)))  // 헬스 체크
            .service(
                web::resource("/api/search")
                    .route(web::post().to(search_similar_video))  // 유사도 검색 API
            )
            .service(
                web::resource("/api/youtube/search")
                    .route(web::post().to(search_youtube_videos))  // YouTube 검색 API
            )
            .service(
                web::resource("/api/channel/info")
                    .route(web::post().to(get_channel_info))  // 채널 정보 API
            )
            .service(
                web::resource("/api/channel/save")
                    .route(web::post().to(save_channel_embeddings))  // 채널 저장 API
            )
            .service(
                web::resource("/api/transcript")
                    .route(web::post().to(get_youtube_transcript))  // 자막 API
            )
    })
    .bind("127.0.0.1:8080")?  // 8080 포트에 바인딩
    .run()  // 서버 실행
    .await  // 비동기 실행 완료까지 대기
} 