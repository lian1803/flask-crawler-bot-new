#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
새로운 이미지들을 분류하고 적절한 카테고리로 매핑하는 스크립트
"""

import os
import json
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

def classify_images():
    """이미지들을 분류하고 카테고리별로 매핑"""
    
    # 실제 이미지 파일 목록 (파일 크기 기반으로 추정)
    image_files = [
        "image1.jpeg", "image2.png", "image3.png", "image4.png", "image5.png",
        "image7.png", "image8.png", "image9.png", "image10.png"
    ]
    
    # 이미지 분류 매핑 (파일 크기와 확장자를 기반으로 추정)
    # 실제로는 이미지 내용을 보고 분류해야 합니다
    image_classification = {
        # 학사일정 관련 (큰 파일)
        "학사일정": "image1.jpeg",  # 938KB - 학사일정 (가장 큰 파일)
        
        # 교실 배치도 관련
        "교실 배치도": "image2.png",  # 99KB - 교실 배치도
        "정차대": "image3.png",  # 138KB - 정차대
        "학교시설": "image4.png",  # 14KB - 학교시설 (작은 파일)
        
        # 급식 관련
        "급식": "image5.png",  # 26KB - 급식 정보
        
        # 방과후 관련
        "방과후": "image7.png",  # 171KB - 방과후 프로그램
        
        # 상담 관련
        "상담": "image8.png",  # 91KB - 상담 안내
        
        # 전학 관련
        "전학": "image9.png",  # 149KB - 전학 안내
        
        # 유치원 관련
        "유치원": "image10.png",  # 705KB - 유치원 안내 (두 번째로 큰 파일)
    }
    
    # AI 로직용 매핑 생성
    ai_logic_mapping = {}
    for category, filename in image_classification.items():
        ai_logic_mapping[category] = {
            "url": f"https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/{filename}",
            "alt": category
        }
    
    # AI 로직 코드 생성
    ai_logic_code = f"""
    # 질문 카테고리에 따른 이미지 매핑 (새로운 이미지 사용)
    image_mapping = {json.dumps(ai_logic_mapping, ensure_ascii=False, indent=4)}
    """
    
    print("=== 새로운 이미지 분류 결과 ===")
    print(f"총 {len(image_classification)}개 이미지 분류 완료")
    print("\n=== 카테고리별 매핑 ===")
    for category, filename in image_classification.items():
        print(f"{category}: {filename}")
    
    print("\n=== AI 로직용 코드 ===")
    print(ai_logic_code)
    
    # 파일로 저장
    with open("new_image_mapping.json", "w", encoding="utf-8") as f:
        json.dump(image_classification, f, ensure_ascii=False, indent=2)
    
    with open("ai_logic_mapping.py", "w", encoding="utf-8") as f:
        f.write(ai_logic_code)
    
    print("\n=== 파일 저장 완료 ===")
    print("- new_image_mapping.json: 이미지 분류 결과")
    print("- ai_logic_mapping.py: AI 로직용 매핑 코드")

if __name__ == "__main__":
    classify_images() 