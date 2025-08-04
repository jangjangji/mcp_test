import torch
import clip
import cv2
import numpy as np
from PIL import Image
import os
from typing import List, Tuple, Dict
import json
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Supabase 클라이언트 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def numpy_to_vector_string(arr: np.ndarray) -> str:
    """numpy 배열을 Supabase vector 형식의 문자열로 변환"""
    return '[' + ','.join(map(str, arr.flatten())) + ']'

class VideoSearchSystem:
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        """CLIP 기반 비디오 검색 시스템 초기화"""
        self.device = device
        print(f"🔧 CLIP 모델 로딩 중... (디바이스: {device})")
        
        # CLIP 모델 로드
        self.model, self.preprocess = clip.load("ViT-B/32", device=device)
        print("✅ CLIP 모델 로딩 완료!")
        
    def extract_frames(self, video_path: str, fps: int = 2) -> List[Tuple[float, np.ndarray]]:
        """비디오에서 프레임 추출 (1초당 2프레임으로 증가)"""
        print(f"🎬 프레임 추출 중: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"비디오 파일을 열 수 없습니다: {video_path}")
        
        frames = []
        frame_count = 0
        fps_video = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps_video / fps)  # 1초당 2프레임
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                # BGR to RGB 변환
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                timestamp = frame_count / fps_video
                frames.append((timestamp, frame_rgb))
                
            frame_count += 1
            
        cap.release()
        print(f"✅ {len(frames)}개 프레임 추출 완료 (1초당 {fps}프레임)")
        return frames
    
    def encode_frames(self, frames: List[Tuple[float, np.ndarray]]) -> List[Tuple[float, np.ndarray]]:
        """프레임들을 CLIP으로 인코딩 (정규화 포함)"""
        print("🔍 프레임 인코딩 중...")
        
        encoded_frames = []
        for timestamp, frame in frames:
            # PIL Image로 변환
            pil_image = Image.fromarray(frame)
            
            # CLIP 전처리 및 인코딩
            image_input = self.preprocess(pil_image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                # L2 정규화 적용
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                image_features = image_features.cpu().numpy()
            
            encoded_frames.append((timestamp, image_features))
            
        print(f"✅ {len(encoded_frames)}개 프레임 인코딩 완료")
        return encoded_frames
    
    def encode_text(self, text: str) -> np.ndarray:
        """텍스트를 CLIP으로 인코딩 (정규화 포함)"""
        text_input = clip.tokenize([text]).to(self.device)
        
        with torch.no_grad():
            text_features = self.model.encode_text(text_input)
            # L2 정규화 적용
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            text_features = text_features.cpu().numpy()
            
        return text_features
    
    def add_video_to_db(self, video_path: str, video_id: str = None) -> str:
        """비디오를 Supabase DB에 추가"""
        if video_id is None:
            video_id = os.path.basename(video_path)
            
        print(f"📹 비디오 DB 추가 중: {video_id}")
        
        # 이미 저장된 비디오인지 확인
        try:
            existing = supabase.table("video_frames").select("video_id").eq("video_id", video_id).limit(1).execute()
            if existing.data:
                print(f"⚠️ 이미 저장된 비디오입니다: {video_id}")
                return video_id
        except Exception as e:
            print(f"⚠️ 기존 데이터 확인 중 오류: {str(e)}")
        
        # 프레임 추출
        frames = self.extract_frames(video_path)
        
        # 프레임 인코딩
        encoded_frames = self.encode_frames(frames)
        
        # Supabase DB에 저장
        saved_count = 0
        for timestamp, embedding in encoded_frames:
            try:
                # 임베딩을 Supabase vector 형식으로 변환
                embedding_vector = numpy_to_vector_string(embedding)
                
                supabase.table("video_frames").insert({
                    "video_id": video_id,
                    "video_path": video_path,
                    "frame_timestamp": timestamp,
                    "embedding": embedding_vector,
                    "added_time": datetime.now().isoformat()
                }).execute()
                saved_count += 1
            except Exception as e:
                print(f"❌ 프레임 저장 실패 (timestamp: {timestamp}): {str(e)}")
                continue
        
        print(f"✅ 비디오 '{video_id}' DB 저장 완료 ({saved_count}개 프레임)")
        return video_id
    
    def search_video_in_db(self, query: str, top_k: int = 5) -> List[Dict]:
        """텍스트 쿼리로 DB에서 비디오 검색"""
        print(f"🔍 DB 검색 중: '{query}'")
        
        # 텍스트 인코딩
        text_features = self.encode_text(query)
        
        # Supabase RPC 호출 (유사도 검색)
        try:
            # 텍스트 임베딩을 vector 형식으로 변환
            text_vector = numpy_to_vector_string(text_features)
            
            response = supabase.rpc("match_video_frames", {
                "input_vector": text_vector,
                "match_count": top_k
            }).execute()
            
            if response.data:
                results = []
                for item in response.data:
                    results.append({
                        "video_id": item.get("video_id"),
                        "video_path": item.get("video_path"),
                        "timestamp": item.get("frame_timestamp"),
                        "similarity": item.get("similarity", 0.0)
                    })
                
                # 유사도 점수 개선 (0-1 범위로 정규화)
                max_similarity = max([r["similarity"] for r in results]) if results else 1.0
                for result in results:
                    result["similarity"] = max(0.0, min(1.0, result["similarity"] / max_similarity))
                
                print(f"✅ 검색 완료: {len(results)}개 결과")
                return results
            else:
                print("❌ 검색 결과가 없습니다")
                return []
                
        except Exception as e:
            print(f"❌ DB 검색 실패: {str(e)}")
            return []
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """코사인 유사도 계산"""
        return np.dot(vec1.flatten(), vec2.flatten()) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def format_timestamp(self, seconds: float) -> str:
        """초를 HH:MM:SS 형식으로 변환"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def clear_video_from_db(self, video_id: str) -> bool:
        """DB에서 특정 비디오 데이터 삭제"""
        try:
            supabase.table("video_frames").delete().eq("video_id", video_id).execute()
            print(f"✅ 비디오 '{video_id}' 데이터 삭제 완료")
            return True
        except Exception as e:
            print(f"❌ 비디오 삭제 실패: {str(e)}")
            return False


# 사용 예시
def demo():
    """데모 실행"""
    print("🚀 CLIP 기반 비디오 검색 시스템 데모")
    print("=" * 50)
    
    # 시스템 초기화
    system = VideoSearchSystem()
    
    # 기존 데이터 삭제 (새로운 설정으로 테스트하기 위해)
    system.clear_video_from_db("dog_video")
    
    # dog.mp4 비디오 추가
    video_id = system.add_video_to_db("video/dog.mp4", "dog_video")
    
    # 검색 예시
    queries = [
        "강아지가 물속에서 헤엄치는 장면",
        "강아지가 물속에서 공을 무는 장면",
        "강아지가 물에서 놀고 있는 장면"
    ]
    
    for query in queries:
        print(f"\n🔍 검색: '{query}'")
        results = system.search_video_in_db(query, top_k=3)
        
        for i, result in enumerate(results):
            timestamp = system.format_timestamp(result["timestamp"])
            print(f"  {i+1}. {result['video_id']} - {timestamp} (유사도: {result['similarity']:.3f})")

if __name__ == "__main__":
    demo()
