import time
import openai
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

def test_semantic_chunking(transcript: str, similarity_threshold: float = 0.7) -> dict:
    """시맨틱 청킹 함수를 테스트하고 각 단계별 결과를 반환"""
    
    # 1. 문장 분리 테스트
    sentences = re.split(r'[.!?,]+', transcript)
    sentences = [s.strip() for s in sentences if len(s.strip()) >= 3]  # 최소 3자로 변경
    
    if len(sentences) <= 1:
        return {"error": "문장이 부족합니다"}
    
    # 2. 문장별 임베딩 테스트
    embeddings = []
    valid_sentences = []
    
    for i, sentence in enumerate(sentences):
        try:
            time.sleep(0.1)
            embedding_response = openai.embeddings.create(
                input=sentence,
                model="text-embedding-3-small"
            )
            embedding = embedding_response.data[0].embedding
            embeddings.append(embedding)
            valid_sentences.append(sentence)
        except Exception as e:
            continue
    
    if len(embeddings) < 2:
        return {"error": "임베딩된 문장이 부족합니다"}
    
    # 3. 유사도 계산 테스트
    embeddings_array = np.array(embeddings)
    similarity_matrix = cosine_similarity(embeddings_array)
    
    # 4. 클러스터링 테스트
    chunks_with_embeddings = []
    used_indices = set()
    
    for i in range(len(valid_sentences)):
        if i in used_indices:
            continue
            
        cluster_indices = [i]
        used_indices.add(i)
        
        for j in range(i + 1, len(valid_sentences)):
            if j in used_indices:
                continue
                
            if similarity_matrix[i][j] >= similarity_threshold:
                cluster_indices.append(j)
                used_indices.add(j)
        
        cluster_sentences = [valid_sentences[idx] for idx in cluster_indices]
        chunk_text = " ".join(cluster_sentences)
        
        if len(chunk_text.strip()) >= 20:
            chunk_embedding = embeddings[cluster_indices[0]]
            chunks_with_embeddings.append((chunk_text.strip(), chunk_embedding))
    
    # 5. 결과 요약
    result = {
        "total_sentences": len(sentences),
        "valid_sentences": len(valid_sentences),
        "embeddings_created": len(embeddings),
        "similarity_threshold": similarity_threshold,
        "chunks_created": len(chunks_with_embeddings),
        "chunks": []
    }
    
    for i, (chunk_text, embedding) in enumerate(chunks_with_embeddings):
        result["chunks"].append({
            "chunk_id": i+1,
            "text": chunk_text,
            "text_length": len(chunk_text),
            "embedding_dimension": len(embedding) if embedding else 0
        })
    
    return result


def load_cooking_transcript():
    """요리 자막 파일을 읽어서 반환"""
    try:
        with open('cooking_transcript.txt', 'r', encoding='utf-8') as f:
            transcript = f.read()
        print(f"📖 요리 자막 파일 읽기 완료: {len(transcript)}자")
        return transcript
    except Exception as e:
        print(f"❌ 요리 자막 파일 읽기 실패: {str(e)}")
        return None

def run_tests():
    """요리 자막 파일 시맨틱 청킹 테스트 실행"""
    print("🚀 요리 자막 시맨틱 청킹 테스트 시작")
    print("=" * 60)
    
    # 요리 자막 파일 테스트
    print(f"\n🧪 테스트: cooking_transcript (실제 요리 영상 자막)")
    print("-" * 40)
    
    cooking_transcript = load_cooking_transcript()
    if cooking_transcript:
        try:
            result = test_semantic_chunking(cooking_transcript, similarity_threshold=0.5)  # 0.7에서 0.5로 낮춤
            
            if "error" not in result:
                print(f"📊 요리 자막 시맨틱 청킹 결과:")
                print(f"   총 문장 수: {result['total_sentences']}개")
                print(f"   생성된 청크 수: {result['chunks_created']}개")
                print(f"   유사도 임계값: {result['similarity_threshold']}")
                
                if result['chunks']:
                    print(f"\n🎯 각 청크별 문장 수:")
                    for chunk in result['chunks']:
                        # 청크 텍스트를 다시 문장으로 분리해서 실제 문장 수 계산
                        chunk_sentences = re.split(r'[.!?,]+', chunk['text'])
                        chunk_sentences = [s.strip() for s in chunk_sentences if len(s.strip()) >= 3]
                        print(f"   청크 {chunk['chunk_id']}: {len(chunk_sentences)}개 문장")
            else:
                print(f"❌ 요리 자막 테스트 실패: {result['error']}")
                
        except Exception as e:
            print(f"❌ 요리 자막 테스트 중 오류 발생: {str(e)}")
    else:
        print("❌ 요리 자막 파일을 읽을 수 없어서 테스트를 건너뜁니다.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    run_tests()