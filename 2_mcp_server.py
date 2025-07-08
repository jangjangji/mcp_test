from mcp.server.fastmcp import FastMCP
import time
import openai
from youtube_transcript_api._api import YouTubeTranscriptApi
from supabase import create_client, Client
import xml.etree.ElementTree as ET
from datetime import datetime
import requests
import re
from dotenv import load_dotenv
import os
import numpy as np
load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_URL = 'https://www.googleapis.com/youtube/v3'
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# Create an MCP server
mcp = FastMCP("youtube_agent_server")



### Tool 1 : 유튜브 영상 URL에 대한 자막을 가져옵니다.

@mcp.tool()
def get_youtube_transcript(url: str) -> str:
    """ 유튜브 영상 URL에 대한 자막을 가져옵니다."""
    
    # 1. 유튜브 URL에서 비디오 ID를 추출합니다.
    video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    if not video_id_match:
        raise ValueError("유효하지 않은 YouTube URL이 제공되었습니다")
    video_id = video_id_match.group(1)
    
    languages = ["ko", "en"]
    # 2. youtube_transcript_api를 사용하여 자막을 가져옵니다.
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        
        # 3. 자막 목록의 'text' 부분을 하나의 문자열로 결합합니다.
        transcript_text = " ".join([entry["text"] for entry in transcript_list])
        return transcript_text

    except Exception as e:
        raise RuntimeError(f"비디오 ID '{video_id}'에 대한 자막을 찾을 수 없거나 사용할 수 없습니다.{e}")


### Tool 2 : 유튜브에서 특정 키워드로 동영상을 검색하고 세부 정보를 가져옵니다
@mcp.tool()
def search_youtube_videos(query: str) :
    """유튜브에서 특정 키워드로 동영상을 검색하고 세부 정보를 가져옵니다"""
    try:
        # 1. 동영상 검색
        max_results: int = 20
        search_url = f"{YOUTUBE_API_URL}/search?part=snippet&q={requests.utils.quote(query)}&type=video&maxResults={max_results}&key={YOUTUBE_API_KEY}"
        print(f"Searching YouTube with URL: {search_url}")

        search_response = requests.get(search_url)
        search_data = search_response.json()
        video_ids = [item['id']['videoId'] for item in search_data.get('items', [])]

        if not video_ids:
            print("No videos found for the query.")
            return []

        video_details_url = f"{YOUTUBE_API_URL}/videos?part=snippet,statistics&id={','.join(video_ids)}&key={YOUTUBE_API_KEY}"
        print(f"영상 정보 가져오는 중: {video_details_url}")
        details_response = requests.get(video_details_url)
        details_response.raise_for_status()
        details_data = details_response.json()

        videos = []
        for item in details_data.get('items', []):
            snippet = item.get('snippet', {})
            statistics = item.get('statistics', {})
            thumbnails = snippet.get('thumbnails', {})
            high_thumbnail = thumbnails.get('high', {}) 
            view_count = statistics.get('viewCount')
            like_count = statistics.get('likeCount')

            video_card = {
                "title": snippet.get('title', 'N/A'),
                "publishedDate": snippet.get('publishedAt', ''),
                "channelName": snippet.get('channelTitle', 'N/A'),
                "channelId": snippet.get('channelId', ''),
                "thumbnailUrl": high_thumbnail.get('url', ''),
                "viewCount": int(view_count) if view_count is not None else None,
                "likeCount": int(like_count) if like_count is not None else None,
                "url": f"https://www.youtube.com/watch?v={item.get('id', '')}",
            }
            videos.append(video_card)

        if not videos:
            print("No video details could be fetched.")
            return []

        return videos

    except Exception as e:
        print(f"Error: {e}")
        return []
    

### Tool 3 : YouTube 동영상 URL로부터 채널 정보와 최근 5개의 동영상을 가져옵니다
@mcp.tool()
def get_channel_info(video_url: str) -> dict:
    """YouTube 동영상 URL로부터 채널 정보와 최근 5개의 동영상을 가져옵니다"""
    def extract_video_id(url):
        match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
        return match.group(1) if match else None

    def fetch_recent_videos(channel_id):
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            response = requests.get(rss_url)
            if response.status_code != 200:
                return []

            root = ET.fromstring(response.text)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            videos = []

            for entry in root.findall('.//atom:entry', ns)[:5]:  
                title = entry.find('./atom:title', ns).text
                link = entry.find('./atom:link', ns).attrib['href']
                published = entry.find('./atom:published', ns).text
                videos.append({
                    'title': title,
                    'link': link,
                    'published': published,
                    'updatedDate': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

            return videos
        except:
            return []

    video_id = extract_video_id(video_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL")

    video_api = f"{YOUTUBE_API_URL}/videos?part=snippet,statistics&id={video_id}&key={YOUTUBE_API_KEY}"
    video_data = requests.get(video_api).json()
    if not video_data.get('items'):
        raise ValueError("No video found")

    video_info = video_data['items'][0]
    channel_id = video_info['snippet']['channelId']

    channel_api = f"{YOUTUBE_API_URL}/channels?part=snippet,statistics&id={channel_id}&key={YOUTUBE_API_KEY}"
    channel_data = requests.get(channel_api).json()['items'][0]

    return {
        'channelTitle': channel_data['snippet']['title'],
        'channelUrl': f"https://www.youtube.com/channel/{channel_id}",
        'subscriberCount': channel_data['statistics'].get('subscriberCount', '0'),
        'viewCount': channel_data['statistics'].get('viewCount', '0'),
        'videoCount': channel_data['statistics'].get('videoCount', '0'),
        'videos': fetch_recent_videos(channel_id)
    }


# 이미 상단에 import, 환경설정, supabase client 생성이 있으므로 아래 중복 제거

@mcp.tool()
def save_channel_youtube_embeddings(channel_id: str) -> str:
    """YouTube 채널 ID 기반으로 100개 영상의 title을 임베딩하고 supabase에 저장"""
    openai.api_key = os.getenv("OPENAI_API_KEY")
    max_results = 3
    video_ids = []
    next_page_token = ""

    # 1. 채널 영상 videoId 수집
    while len(video_ids) < max_results:
        search_url = (
            f"{YOUTUBE_API_URL}/search?part=snippet&channelId={channel_id}"
            f"&maxResults=50&order=date&type=video&key={YOUTUBE_API_KEY}"
        )
        if next_page_token:
            search_url += f"&pageToken={next_page_token}"
        resp = requests.get(search_url)
        data = resp.json()
        for item in data.get("items", []):
            vid = item["id"]["videoId"]
            if vid not in video_ids:
                video_ids.append(vid)
                if len(video_ids) >= max_results:
                    break
        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    print(f"[✔] 총 {len(video_ids)}개 영상 수집 완료")

    if not video_ids:
        return "영상이 없습니다."

    count = 0
    # 2. 상세 정보 조회 및 임베딩/저장
    for i in range(0, len(video_ids), 50): ## range(start, stop, step) 시작,끝값,간격
        batch_ids = video_ids[i:i + 50]
        details_url = f"{YOUTUBE_API_URL}/videos?part=snippet&id={','.join(batch_ids)}&key={YOUTUBE_API_KEY}"
        details_resp = requests.get(details_url) 
        details_resp.raise_for_status() ## HTTP 에러 발생 시 예외 발생
        video_data = details_resp.json()

        for video in video_data.get("items", []):
            video_id = video["id"]
            title = video["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={video_id}"

            # 중복 확인
            try:
                existing = supabase.table("youtube_videos").select("video_id").eq("video_id", video_id).execute()
                if existing.data:
                    print(f"[SKIP] 중복: {video_id}")
                    continue
            except Exception as e:
                print(f"[ERR] 중복 확인 실패: {e}")
                continue

            # OpenAI 임베딩
            try:
                time.sleep(1)  # rate limit 회피
                embedding = openai.embeddings.create(
                    input=title,
                    model="text-embedding-3-small"
                ).data[0].embedding
            except Exception as e:
                print(f"[ERR] 임베딩 실패: {title} - {e}")
                continue

            # Supabase 저장
            try:
                supabase.table("youtube_videos").insert({
                    "video_id": video_id,
                    "url": url,
                    "title": title,
                    "embedding": embedding
                }).execute()
                print(f"[SAVE] 저장 완료: {video_id}")
                count += 1
            except Exception as e:
                print(f"[ERR] 저장 실패: {video_id} - {e}")
                continue

    return f"총 {count}개 영상이 저장되었습니다."


@mcp.tool()
def search_similar_youtube_video(query: str) -> dict:
    """검색어를 임베딩하고 Supabase RPC를 통해 가장 유사한 영상 1개를 반환"""

    try:
        # 1. OpenAI를 사용해 쿼리 임베딩 생성
        embedding_response = openai.embeddings.create(
            input=query,
            model="text-embedding-3-small"  # 또는 text-embedding-ada-002
        )
        embedding = embedding_response.data[0].embedding

        # 2. Supabase RPC 호출 (input_vector는 JSON 형태 리스트 그대로 넘김)
        response = supabase.rpc("match_youtube_video", {
            "input_vector": embedding
        }).execute()

        # 3. 결과 반환
        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            return {"error": "No similar video found."}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    print("Starting MCP server...")
    mcp.run()