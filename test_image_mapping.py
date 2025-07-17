#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
새로운 이미지 매핑을 테스트하는 스크립트
"""

import requests
import json

def test_image_urls():
    """이미지 URL들이 실제로 접근 가능한지 테스트"""
    
    # 이미지 매핑
    image_mapping = {
        "학사일정": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image1.jpeg",
        "교실 배치도": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image2.png",
        "정차대": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image3.png",
        "학교시설": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image4.png",
        "급식": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image5.png",
        "방과후": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image7.png",
        "상담": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image8.png",
        "전학": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image9.png",
        "유치원": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image10.png"
    }
    
    print("=== 이미지 URL 접근 테스트 ===")
    
    for category, url in image_mapping.items():
        try:
            response = requests.head(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {category}: 접근 가능")
            else:
                print(f"❌ {category}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {category}: 오류 - {e}")
    
    print("\n=== 테스트 완료 ===")

def test_ai_logic_mapping():
    """AI 로직의 이미지 매핑 테스트"""
    
    # AI 로직에서 사용하는 매핑 구조
    ai_logic_mapping = {
        "학사일정": {
            "url": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image1.jpeg",
            "alt": "학사일정"
        },
        "교실 배치도": {
            "url": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image2.png",
            "alt": "교실 배치도"
        },
        "정차대": {
            "url": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image3.png",
            "alt": "정차대"
        },
        "학교시설": {
            "url": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image4.png",
            "alt": "학교시설"
        },
        "급식": {
            "url": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image5.png",
            "alt": "급식"
        },
        "방과후": {
            "url": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image7.png",
            "alt": "방과후"
        },
        "상담": {
            "url": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image8.png",
            "alt": "상담"
        },
        "전학": {
            "url": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image9.png",
            "alt": "전학"
        },
        "유치원": {
            "url": "https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/image10.png",
            "alt": "유치원"
        }
    }
    
    print("=== AI 로직 매핑 구조 테스트 ===")
    print(json.dumps(ai_logic_mapping, ensure_ascii=False, indent=2))
    
    # 질문별 이미지 매칭 테스트
    test_questions = [
        "학사일정 알려줘",
        "교실 배치도 보여줘",
        "정차대 어디야",
        "급식 메뉴 뭐야",
        "방과후 프로그램",
        "상담 받고 싶어",
        "전학 절차",
        "유치원 정보",
        "학교시설 이용시간"
    ]
    
    print("\n=== 질문별 이미지 매칭 테스트 ===")
    for question in test_questions:
        question_lower = question.lower()
        
        if "학사일정" in question_lower or "개학" in question_lower or "방학" in question_lower:
            category = "학사일정"
        elif "교실" in question_lower or "배치" in question_lower:
            category = "교실 배치도"
        elif "정차" in question_lower or "버스" in question_lower:
            category = "정차대"
        elif "급식" in question_lower or "식단" in question_lower or "밥" in question_lower or "점심" in question_lower:
            category = "급식"
        elif "방과후" in question_lower or "늘봄" in question_lower or "돌봄" in question_lower:
            category = "방과후"
        elif "상담" in question_lower or "문의" in question_lower:
            category = "상담"
        elif "전학" in question_lower or "전입" in question_lower or "전출" in question_lower:
            category = "전학"
        elif "유치원" in question_lower or "유아" in question_lower:
            category = "유치원"
        elif "시설" in question_lower:
            category = "학교시설"
        else:
            category = "학사일정"  # 기본값
        
        image_info = ai_logic_mapping[category]
        print(f"질문: {question}")
        print(f"  → 매칭: {category}")
        print(f"  → 이미지: {image_info['url']}")
        print()

if __name__ == "__main__":
    test_image_urls()
    test_ai_logic_mapping() 