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
# .env 파일에서 URL과 키를 가져와서 데이터베이스 클라이언트 생성
SUPABASE_URL = os.getenv("SUPABASE_URL")  # Supabase 프로젝트 URL
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Supabase API 키
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)  # 데이터베이스 클라이언트 생성

def numpy_to_vector_string(arr: np.ndarray) -> str:
    """
    numpy 배열을 Supabase에서 사용하는 vector 형식의 문자열로 변환하는 함수
    
    예시: [1.2, 3.4, 5.6] -> "[1.2,3.4,5.6]"
    """
    # 배열을 1차원으로 펴고, 각 숫자를 문자열로 변환한 후 쉼표로 연결
    return '[' + ','.join(map(str, arr.flatten())) + ']'

class VideoSearchSystem:
    """
    CLIP 기반 비디오 검색 시스템 클래스
    비디오를 분석하고 텍스트로 검색할 수 있게 해주는 시스템
    """
    
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        """
        시스템 초기화 함수
        device: GPU가 있으면 "cuda", 없으면 "cpu" 사용
        """
        self.device = device  # 사용할 디바이스 저장
        print(f"🔧 CLIP 모델 로딩 중... (디바이스: {device})")
        
        # CLIP 모델을 메모리에 로드
        # "ViT-B/32"는 CLIP의 모델 종류 중 하나 (Vision Transformer)
        self.model, self.preprocess = clip.load("ViT-B/32", device=device)
        print("✅ CLIP 모델 로딩 완료!")
        
    def extract_frames(self, video_path: str, fps: int = 2) -> List[Tuple[float, np.ndarray]]:
        """
        비디오 파일에서 프레임들을 추출하는 함수
        
        video_path: 비디오 파일 경로
        fps: 1초당 몇 개의 프레임을 추출할지 (기본값: 2개)
        반환값: (타임스탬프, 프레임 이미지) 튜플들의 리스트
        """
        print(f"🎬 프레임 추출 중: {video_path}")
        
        # OpenCV로 비디오 파일 열기
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"비디오 파일을 열 수 없습니다: {video_path}")
        
        frames = []  # 추출된 프레임들을 저장할 리스트
        frame_count = 0  # 현재 프레임 번호
        fps_video = cap.get(cv2.CAP_PROP_FPS)  # 비디오의 원본 FPS (초당 프레임 수)
        frame_interval = int(fps_video / fps)  # 몇 프레임마다 하나를 추출할지 계산
        
        # 비디오의 모든 프레임을 순서대로 읽기
        while True:
            ret, frame = cap.read()  # 한 프레임 읽기
            if not ret:  # 더 이상 읽을 프레임이 없으면 종료
                break
                
            # frame_interval마다 프레임을 저장 (예: 30fps 비디오에서 2fps로 추출하려면 15프레임마다 하나 저장)
            if frame_count % frame_interval == 0:
                # OpenCV는 BGR 색상 형식을 사용하지만, CLIP은 RGB를 사용하므로 변환
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                timestamp = frame_count / fps_video  # 현재 프레임의 시간 (초 단위)
                frames.append((timestamp, frame_rgb))  # (시간, 이미지) 튜플로 저장
                
            frame_count += 1
            
        cap.release()  # 비디오 파일 닫기
        print(f"✅ {len(frames)}개 프레임 추출 완료 (1초당 {fps}프레임)")
        return frames
    
    def encode_frames(self, frames: List[Tuple[float, np.ndarray]]) -> List[Tuple[float, np.ndarray]]:
        """
        추출된 프레임들을 CLIP 모델로 인코딩하는 함수
        이미지를 숫자 벡터로 변환하여 검색 가능하게 만듦
        
        frames: (타임스탬프, 프레임 이미지) 튜플들의 리스트
        반환값: (타임스탬프, 인코딩된 벡터) 튜플들의 리스트
        """
        print("🔍 프레임 인코딩 중...")
        
        encoded_frames = []  # 인코딩된 프레임들을 저장할 리스트
        
        # 각 프레임을 하나씩 처리
        for timestamp, frame in frames:
            # numpy 배열을 PIL Image 객체로 변환 (CLIP이 PIL Image를 요구함)
            pil_image = Image.fromarray(frame)
            
            # CLIP 모델이 이해할 수 있는 형태로 이미지 전처리
            # unsqueeze(0)는 배치 차원을 추가하는 것 (1개 이미지를 1개 배치로 만듦)
            image_input = self.preprocess(pil_image).unsqueeze(0).to(self.device)
            
            # CLIP 모델로 이미지를 벡터로 인코딩
            with torch.no_grad():  # 그래디언트 계산 비활성화 (메모리 절약)
                image_features = self.model.encode_image(image_input)  # 이미지를 512차원 벡터로 변환
                # L2 정규화: 벡터의 길이를 1로 만듦 (유사도 계산을 위해)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                image_features = image_features.cpu().numpy()  # GPU에서 CPU로, PyTorch에서 numpy로 변환
            
            encoded_frames.append((timestamp, image_features))  # (시간, 벡터) 튜플로 저장
            
        print(f"✅ {len(encoded_frames)}개 프레임 인코딩 완료")
        return encoded_frames
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        텍스트를 CLIP 모델로 인코딩하는 함수
        텍스트를 숫자 벡터로 변환하여 이미지와 비교 가능하게 만듦
        
        text: 검색할 텍스트
        반환값: 인코딩된 텍스트 벡터
        """
        # CLIP 모델이 이해할 수 있는 형태로 텍스트 토큰화
        text_input = clip.tokenize([text]).to(self.device)
        
        # CLIP 모델로 텍스트를 벡터로 인코딩
        with torch.no_grad():  # 그래디언트 계산 비활성화
            text_features = self.model.encode_text(text_input)  # 텍스트를 512차원 벡터로 변환
            # L2 정규화: 벡터의 길이를 1로 만듦
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            text_features = text_features.cpu().numpy()  # GPU에서 CPU로, PyTorch에서 numpy로 변환
            
        return text_features
    
    def add_video_to_db(self, video_path: str, video_id: str = None) -> str:
        """
        비디오를 데이터베이스에 추가하는 함수
        비디오를 분석하고 프레임들을 데이터베이스에 저장
        
        video_path: 비디오 파일 경로
        video_id: 비디오 식별자 (없으면 파일명 사용)
        반환값: 저장된 비디오의 ID
        """
        # video_id가 없으면 파일명을 ID로 사용
        if video_id is None:
            video_id = os.path.basename(video_path)
            
        print(f"📹 비디오 DB 추가 중: {video_id}")
        
        # 이미 저장된 비디오인지 확인 (중복 방지)
        try:
            # 데이터베이스에서 같은 video_id가 있는지 확인
            existing = supabase.table("video_frames").select("video_id").eq("video_id", video_id).limit(1).execute()
            if existing.data:  # 이미 저장된 비디오가 있으면
                print(f"⚠️ 이미 저장된 비디오입니다: {video_id}")
                return video_id
        except Exception as e:
            print(f"⚠️ 기존 데이터 확인 중 오류: {str(e)}")
        
        # 1단계: 비디오에서 프레임 추출
        frames = self.extract_frames(video_path)
        
        # 2단계: 추출된 프레임들을 CLIP으로 인코딩
        encoded_frames = self.encode_frames(frames)
        
        # 3단계: 인코딩된 프레임들을 Supabase 데이터베이스에 저장
        saved_count = 0  # 성공적으로 저장된 프레임 수
        for timestamp, embedding in encoded_frames:
            try:
                # numpy 배열을 Supabase vector 형식의 문자열로 변환
                embedding_vector = numpy_to_vector_string(embedding)
                
                # 데이터베이스에 프레임 정보 저장
                supabase.table("video_frames").insert({
                    "video_id": video_id,           # 비디오 식별자
                    "video_path": video_path,       # 비디오 파일 경로
                    "frame_timestamp": timestamp,   # 프레임 시간
                    "embedding": embedding_vector,   # 인코딩된 벡터
                    "added_time": datetime.now().isoformat()  # 저장 시간
                }).execute()
                saved_count += 1
            except Exception as e:
                print(f"❌ 프레임 저장 실패 (timestamp: {timestamp}): {str(e)}")
                continue
        
        print(f"✅ 비디오 '{video_id}' DB 저장 완료 ({saved_count}개 프레임)")
        return video_id
    
    def search_video_in_db(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        텍스트 쿼리로 데이터베이스에서 비디오를 검색하는 함수
        
        query: 검색할 텍스트
        top_k: 반환할 최대 결과 수
        반환값: 검색 결과 리스트 (각 결과는 딕셔너리)
        """
        print(f"🔍 DB 검색 중: '{query}'")
        
        # 1단계: 검색 텍스트를 CLIP으로 인코딩
        text_features = self.encode_text(query)
        
        # 2단계: Supabase의 벡터 유사도 검색 함수 호출
        try:
            # 텍스트 임베딩을 Supabase vector 형식으로 변환
            text_vector = numpy_to_vector_string(text_features)
            
            print(f"🔍 검색 텍스트: '{query}'")
            print(f"🔍 텍스트 벡터 차원: {text_features.shape}")
            print(f"🔍 벡터 값 (처음 5개): {text_features[:5]}")
            
            # Supabase의 match_video_frames 함수 호출 (PostgreSQL 함수)
            # 이 함수는 벡터 유사도를 계산하여 가장 유사한 프레임들을 반환
            print(f"🔍 match_video_frames 함수 호출 시작...")
            print(f"🔍 입력 벡터 길이: {len(text_vector)}")
            print(f"🔍 match_count: {top_k}")
            
            response = supabase.rpc("match_video_frames", {
                "input_vector": text_vector,  # 검색할 텍스트 벡터
                "match_count": top_k          # 반환할 결과 수
            }).execute()
            
            print(f"🔍 Supabase 응답: {response.data}")
            print(f"🔍 응답 데이터 타입: {type(response.data)}")
            if response.data:
                print(f"🔍 응답 데이터 길이: {len(response.data)}")
                for i, item in enumerate(response.data):
                    print(f"🔍 결과 {i+1}: video_id={item.get('video_id')}, similarity={item.get('similarity')}")
            
            # 3단계: 검색 결과 처리
            if response.data:  # 검색 결과가 있으면
                results = []
                for item in response.data:
                    # 각 검색 결과를 딕셔너리 형태로 변환
                    results.append({
                        "video_id": item.get("video_id"),           # 비디오 ID
                        "video_path": item.get("video_path"),       # 비디오 경로
                        "timestamp": item.get("frame_timestamp"),   # 프레임 시간
                        "similarity": item.get("similarity", 0.0)   # 유사도 점수
                    })
                
                # Supabase에서 이미 정규화된 유사도 점수를 반환하므로 추가 정규화 불필요
                # 유사도 점수는 그대로 사용 (0-1 범위)
                
                print(f"✅ 검색 완료: {len(results)}개 결과")
                return results
            else:
                print("❌ 검색 결과가 없습니다")
                return []
                
        except Exception as e:
            print(f"❌ DB 검색 실패: {str(e)}")
            return []
    
    def clear_video_from_db(self, video_id: str) -> bool:
        """
        데이터베이스에서 특정 비디오의 모든 데이터를 삭제하는 함수
        
        video_id: 삭제할 비디오의 ID
        반환값: 삭제 성공 여부
        """
        try:
            # video_id가 일치하는 모든 행을 삭제
            supabase.table("video_frames").delete().eq("video_id", video_id).execute()
            print(f"✅ 비디오 '{video_id}' 데이터 삭제 완료")
            return True
        except Exception as e:
            print(f"❌ 비디오 삭제 실패: {str(e)}")
            return False
    
    def debug_video_embeddings(self, video_id: str):
        """
        특정 비디오의 임베딩 벡터를 디버깅하는 함수
        
        video_id: 확인할 비디오의 ID
        """
        try:
            print(f"🔍 '{video_id}' 비디오의 임베딩 벡터 확인 중...")
            
            # video_frames 테이블에서 해당 비디오의 모든 프레임 조회
            response = supabase.table("video_frames").select("*").eq("video_id", video_id).execute()
            
            if response.data:
                print(f"✅ '{video_id}' 비디오에서 {len(response.data)}개 프레임 발견")
                
                for i, frame in enumerate(response.data[:3]):  # 처음 3개만 출력
                    embedding = frame.get("embedding", "")
                    timestamp = frame.get("frame_timestamp", 0)
                    
                    # 벡터 길이 계산 (대괄호와 쉼표로 분리)
                    vector_length = len(embedding.strip("[]").split(","))
                    
                    print(f"  프레임 {i+1} (시간: {timestamp}):")
                    print(f"    벡터 길이: {vector_length}")
                    print(f"    임베딩 (처음 10개): {embedding[:100]}...")
            else:
                print(f"❌ '{video_id}' 비디오의 프레임을 찾을 수 없습니다")
                
        except Exception as e:
            print(f"❌ 디버깅 실패: {str(e)}")


# 이 파일이 직접 실행될 때만 실행
if __name__ == "__main__":
    print("🚀 VideoSearchSystem 모듈 로드 완료")
