import os
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import openai
from dotenv import load_dotenv
import time

load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

def test_image_embedding(image_path_or_url):
    """이미지 임베딩을 테스트하는 함수"""
    
    try:
        # 이미지 로드
        if image_path_or_url.startswith(('http://', 'https://')):
            # URL에서 이미지 다운로드
            response = requests.get(image_path_or_url, timeout=10)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
        else:
            # 로컬 파일에서 이미지 로드
            image = Image.open(image_path_or_url)
        
        # 이미지 정보 출력
        print(f"이미지 크기: {image.size}")
        print(f"이미지 모드: {image.mode}")
        
        # OpenAI Vision API를 사용한 이미지 분석
        # 먼저 이미지를 base64로 인코딩
        import base64
        from io import BytesIO
        
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        print("OpenAI Vision API 호출 중...")
        
        # OpenAI Vision API로 이미지 분석 (타임아웃 설정)
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "이 이미지에 대해 간단히 설명해주세요. 동물이 있다면 어떤 동물인지 알려주세요."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_str}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=150,
            timeout=30
        )
        
        description = response.choices[0].message.content
        print(f"이미지 분석 결과: {description}")
        
        # 잠시 대기 (API 호출 간격 조절)
        time.sleep(1)
        
        print("텍스트 임베딩 생성 중...")
        # 분석된 텍스트를 임베딩으로 변환
        embedding_response = openai.embeddings.create(
            input=description,
            model="text-embedding-3-small",
            timeout=30
        )
        
        embedding = embedding_response.data[0].embedding
        print(f"임베딩 벡터 크기: {len(embedding)}")
        print(f"임베딩 벡터 (처음 5개): {embedding[:5]}")
        
        return {
            "description": description,
            "embedding": embedding,
            "embedding_size": len(embedding)
        }
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return None

def test_similarity(embedding1, embedding2):
    """두 임베딩 벡터 간의 유사도를 계산"""
    # 코사인 유사도 계산
    dot_product = np.dot(embedding1, embedding2)
    norm1 = np.linalg.norm(embedding1)
    norm2 = np.linalg.norm(embedding2)
    similarity = dot_product / (norm1 * norm2)
    return similarity

if __name__ == "__main__":
    # 테스트 이미지들 (다양한 동물들)
    test_images = [
        "image/lion.jpg",   # 사자
        "image/tiger.jpg",  # 판다  
        "image/dog.jpg",    # 강아지
    ]
    
    embeddings = []
    
    print("=== 이미지 임베딩 테스트 시작 ===\n")
    
    for i, image_path in enumerate(test_images):
        print(f"이미지 {i+1} 처리 중... ({image_path})")
        result = test_image_embedding(image_path)
        if result:
            embeddings.append(result)
            print(f"✅ 이미지 {i+1} 처리 완료")
        else:
            print(f"❌ 이미지 {i+1} 처리 실패")
        print("-" * 50)
    
    # 유사도 테스트
    if len(embeddings) >= 2:
        print("\n=== 유사도 테스트 ===")
        animal_names = ["사자", "판다", "강아지"]
        for i in range(len(embeddings)):
            for j in range(i+1, len(embeddings)):
                similarity = test_similarity(embeddings[i]["embedding"], embeddings[j]["embedding"])
                print(f"{animal_names[i]} vs {animal_names[j]} 유사도: {similarity:.4f}")
                print(f"설명: {embeddings[i]['description'][:80]}...")
                print(f"설명: {embeddings[j]['description'][:80]}...")
                print()
    else:
        print("❌ 유사도 테스트를 위한 충분한 이미지가 처리되지 않았습니다.") 