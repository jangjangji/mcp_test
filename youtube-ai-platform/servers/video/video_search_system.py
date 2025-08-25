# 필요한 라이브러리들을 가져오기
import torch          # 딥러닝 프레임워크 (PyTorch)
import clip           # OpenAI의 CLIP 모델 (이미지와 텍스트를 이해하는 AI)
import cv2            # 컴퓨터 비전 라이브러리 (비디오 처리용)
import numpy as np    # 수치 계산 라이브러리
from PIL import Image # 이미지 처리 라이브러리
import os             # 운영체제 관련 기능 (파일 경로 등)
from typing import List, Tuple, Dict  # 타입 힌트 (코드 가독성 향상)
from datetime import datetime  # 날짜/시간 처리
from supabase import create_client, Client  # Supabase 데이터베이스 연결
from dotenv import load_dotenv  # 환경변수 로드 (.env 파일에서)

# .env 파일에서 환경변수들을 가져오기
load_dotenv()

# Supabase 데이터베이스 연결 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class VideoSearchSystem:
    """
    CLIP 기반 비디오 검색 시스템 클래스
    비디오를 분석하고 텍스트로 검색할 수 있게 해주는 시스템
    """
    
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        print(f"🔧 CLIP 모델 로딩 중... (디바이스: {device})")
        self.model, self.preprocess = clip.load("ViT-B/32", device=device)
        print("✅ CLIP 모델 로딩 완료!")
        
    def extract_frames(self, video_path: str, fps: int = 2) -> List[Tuple[float, np.ndarray]]:
        print(f"🎬 프레임 추출 중: {video_path}")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"비디오 파일을 열 수 없습니다: {video_path}")
        
        frames = []
        frame_count = 0
        fps_video = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps_video / fps)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                timestamp = frame_count / fps_video
                frames.append((timestamp, frame_rgb))
                
            frame_count += 1
            
        cap.release()
        print(f"✅ {len(frames)}개 프레임 추출 완료 (1초당 {fps}프레임)")
        return frames
    
    def encode_frames(self, frames: List[Tuple[float, np.ndarray]]) -> List[Tuple[float, np.ndarray]]:
        print("🔍 프레임 인코딩 중...")
        encoded_frames = []
        for timestamp, frame in frames:
            pil_image = Image.fromarray(frame)
            image_input = self.preprocess(pil_image).unsqueeze(0).to(self.device)
            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                image_features = image_features.cpu().numpy()
            encoded_frames.append((timestamp, image_features))
        print(f"✅ {len(encoded_frames)}개 프레임 인코딩 완료")
        return encoded_frames
    
    def encode_text(self, text: str) -> np.ndarray:
        text_input = clip.tokenize([text]).to(self.device)
        with torch.no_grad():
            text_features = self.model.encode_text(text_input)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            text_features = text_features.cpu().numpy()
        print(f"🔍 encode_text: text_features shape={text_features.shape}")
        return text_features
    
    def add_video_to_db(self, video_path: str, video_id: str = None) -> str:
        if video_id is None:
            video_id = os.path.basename(video_path)
        print(f"📹 비디오 DB 추가 중: {video_id}")
        
        try:
            existing = supabase.table("video_frames").select("video_id").eq("video_id", video_id).limit(1).execute()
            if existing.data:
                print(f"⚠️ 이미 저장된 비디오입니다: {video_id}")
                return video_id
        except Exception as e:
            print(f"⚠️ 기존 데이터 확인 중 오류: {str(e)}")
        
        frames = self.extract_frames(video_path)
        encoded_frames = self.encode_frames(frames)
        
        saved_count = 0
        for timestamp, embedding in encoded_frames:
            try:
                embedding_list = embedding.flatten().tolist()
                supabase.table("video_frames").insert({
                    "video_id": video_id,
                    "video_path": video_path,
                    "frame_timestamp": timestamp,
                    "embedding": embedding_list,
                    "added_time": datetime.now().isoformat()
                }).execute()
                saved_count += 1
            except Exception as e:
                print(f"❌ 프레임 저장 실패 (timestamp: {timestamp}): {str(e)}")
                continue
        
        print(f"✅ 비디오 '{video_id}' DB 저장 완료 ({saved_count}개 프레임)")
        return video_id
    
    def search_video_in_db(self, query: str, top_k: int = 3) -> List[Dict]:
        print(f"🔍 DB 검색 중: '{query}'")
        text_features = self.encode_text(query)
        try:
            print(f"🔍 text_features 원본: {type(text_features)}, shape: {text_features.shape}")
            print(f"🔍 text_features[0] 타입: {type(text_features[0])}, shape: {text_features[0].shape}")
            
            text_vector_list = text_features[0].tolist()
            print(f"🔍 text_vector_list 타입: {type(text_vector_list)}, 길이: {len(text_vector_list)}")
            print(f"🔍 text_vector_list 처음 5개: {text_vector_list[:5]}")
            
            print(f"🔍 match_video_frames 호출 (match_count={top_k})")
            
            response = supabase.rpc("match_video_frames", {
                "input_vector": text_vector_list,
                "match_count": top_k
            }).execute()
            
            print(f"🔍 Supabase 응답: {response.data}")
            if response.data:
                results = []
                for item in response.data:
                    results.append({
                        "video_id": item.get("video_id"),
                        "video_path": item.get("video_path"),
                        "timestamp": item.get("frame_timestamp"),
                        "similarity": item.get("similarity", 0.0)
                    })
                print(f"✅ 검색 완료: {len(results)}개 결과")
                return results
            else:
                print("❌ 검색 결과가 없습니다")
                return []
        except Exception as e:
            print(f"❌ DB 검색 실패: {str(e)}")
            return []
    
    def clear_video_from_db(self, video_id: str) -> bool:
        try:
            supabase.table("video_frames").delete().eq("video_id", video_id).execute()
            print(f"✅ 비디오 '{video_id}' 데이터 삭제 완료")
            return True
        except Exception as e:
            print(f"❌ 비디오 삭제 실패: {str(e)}")
            return False
    
    def debug_video_embeddings(self, video_id: str):
        try:
            print(f"🔍 '{video_id}' 비디오의 임베딩 벡터 확인 중...")
            response = supabase.table("video_frames").select("*").eq("video_id", video_id).execute()
            if response.data:
                print(f"✅ '{video_id}' 비디오에서 {len(response.data)}개 프레임 발견")
                for i, frame in enumerate(response.data[:3]):
                    embedding = frame.get("embedding", [])
                    timestamp = frame.get("frame_timestamp", 0)
                    
                    if isinstance(embedding, list):
                        vector_length = len(embedding)
                        preview = embedding[:10]
                    else:
                        vector_length = len(str(embedding).strip("[]").split(","))
                        preview = str(embedding)[:100]
                    
                    print(f"  프레임 {i+1} (시간: {timestamp}):")
                    print(f"    벡터 길이: {vector_length}")
                    print(f"    임베딩 (처음 10개): {preview}...")
            else:
                print(f"❌ '{video_id}' 비디오의 프레임을 찾을 수 없습니다")
        except Exception as e:
            print(f"❌ 디버깅 실패: {str(e)}")


if __name__ == "__main__":
    print("🚀 VideoSearchSystem 모듈 로드 완료")
