#!/usr/bin/env python3
"""
음식 카테고리별 유튜브 영상 데이터 수집 스크립트
다양한 음식 카테고리와 난이도별로 영상을 수집하여 DB에 저장합니다.
"""

import time
import random
from mcp_server import (
    FOOD_CATEGORIES, 
    search_food_videos_by_category, 
    save_food_category_videos,
    search_similar_youtube_video
)

def collect_food_data():
    """음식 카테고리별 데이터를 수집합니다."""
    
    print("🍳 음식 카테고리별 데이터 수집을 시작합니다...")
    print("=" * 50)
    
    # 각 카테고리별로 데이터 수집
    for category_key, category_info in FOOD_CATEGORIES.items():
        print(f"\n📁 {category_info['name']} 카테고리 처리 중...")
        
        # 난이도별로 데이터 수집
        for difficulty in category_info['difficulty_levels']:
            print(f"  📊 {difficulty} 난이도 영상 수집 중...")
            
            try:
                result = save_food_category_videos(category_key, difficulty)
                print(f"  ✅ {difficulty}: {result}")
                
                # API 호출 제한을 피하기 위한 대기
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                print(f"  ❌ {difficulty} 처리 실패: {str(e)}")
                continue
    
    print("\n🎉 모든 카테고리 데이터 수집 완료!")

def test_search_queries():
    """다양한 검색 쿼리로 테스트를 수행합니다."""
    
    test_queries = [
        # 구체적 요리법 검색
        "제육볶음에 간장 넣는 방법",
        "김치찌개에 돼지고기 넣는 시점",
        "파스타 카르보나라 만들기",
        "스테이크 굽는 온도",
        
        # 재료 중심 검색
        "간장으로 만드는 요리",
        "고추장 활용법",
        "올리브오일 요리법",
        "버터로 만드는 디저트",
        
        # 기법 중심 검색
        "볶음 요리 기법",
        "양념장 만드는 법",
        "육수 내는 방법",
        "반죽하는 기법",
        
        # 난이도별 검색
        "초보자를 위한 요리",
        "셰프의 특별한 요리법",
        "집에서 만드는 레스토랑 요리",
        
        # 음식 종류별 검색
        "한식 레시피",
        "양식 만드는 법",
        "중식 요리법",
        "일식 만들기",
        "베이킹 레시피"
    ]
    
    print("🔍 검색 테스트를 시작합니다...")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i:2d}. 검색어: '{query}'")
        
        try:
            result = search_similar_youtube_video(query)
            
            if "error" in result:
                print(f"    ❌ 검색 실패: {result['error']}")
            else:
                print(f"    ✅ 검색 성공!")
                print(f"    📺 영상: {result.get('video_id', 'N/A')}")
                print(f"    📝 청크: {result.get('chunk_index', 'N/A')}")
                print(f"    🎯 점수: {result.get('score', 'N/A')}")
                print(f"    📄 내용: {result.get('chunk_text', 'N/A')[:100]}...")
            
            # API 호출 제한을 피하기 위한 대기
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            print(f"    ❌ 테스트 실패: {str(e)}")
    
    print("\n🎉 모든 검색 테스트 완료!")

def analyze_data_quality():
    """수집된 데이터의 품질을 분석합니다."""
    
    print("📊 데이터 품질 분석을 시작합니다...")
    print("=" * 50)
    
    # 각 카테고리별 통계
    for category_key, category_info in FOOD_CATEGORIES.items():
        print(f"\n📁 {category_info['name']} 카테고리:")
        
        for difficulty in category_info['difficulty_levels']:
            print(f"  📊 {difficulty} 난이도:")
            
            # 실제로는 DB에서 카테고리별 통계를 조회해야 함
            # 여기서는 예시로 출력
            print(f"    - 영상 수: 예상 10-20개")
            print(f"    - 청크 수: 예상 50-100개")
            print(f"    - 평균 자막 길이: 예상 200-500자")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "collect":
            collect_food_data()
        elif command == "test":
            test_search_queries()
        elif command == "analyze":
            analyze_data_quality()
        else:
            print("사용법: python food_data_collector.py [collect|test|analyze]")
    else:
        print("🍳 음식 데이터 수집 도구")
        print("사용법:")
        print("  python food_data_collector.py collect  - 데이터 수집")
        print("  python food_data_collector.py test     - 검색 테스트")
        print("  python food_data_collector.py analyze  - 데이터 품질 분석") 