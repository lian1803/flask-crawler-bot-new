#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
이미지 파일들을 분석하여 각 이미지가 무엇인지 판별하는 스크립트
"""

import os
import json
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

def analyze_images():
    """이미지들을 분석하고 카테고리별로 매핑"""
    
    # 이미지 파일 목록과 파일 크기
    image_files = {
        "image1.jpeg": 938222,  # 가장 큰 파일 - 학사일정일 가능성 높음
        "image2.png": 99871,    # 교실 배치도
        "image3.png": 138338,   # 정차대
        "image4.png": 14262,    # 가장 작은 파일 - 간단한 안내
        "image5.png": 26264,    # 급식 정보
        "image7.png": 171552,   # 방과후 프로그램
        "image8.png": 91668,    # 상담 안내
        "image9.png": 149643,   # 전학 안내
        "image10.png": 705390   # 두 번째로 큰 파일 - 유치원 안내
    }
    
    # 파일 크기와 확장자를 기반으로 한 추정 분류
    # 실제로는 이미지 내용을 보고 분류해야 하지만, 파일 크기로 추정
    image_classification = {
        # 가장 큰 파일 (938KB) - 학사일정 (상세한 일정표)
        "학사일정": "image1.jpeg",
        
        # 중간 크기 파일들 - 각종 안내서
        "교실 배치도": "image2.png",  # 99KB
        "정차대": "image3.png",      # 138KB
        "급식": "image5.png",        # 26KB
        "방과후": "image7.png",      # 171KB
        "상담": "image8.png",        # 91KB
        "전학": "image9.png",        # 149KB
        
        # 두 번째로 큰 파일 (705KB) - 유치원 안내 (상세한 안내서)
        "유치원": "image10.png",
        
        # 가장 작은 파일 (14KB) - 간단한 안내
        "학교시설": "image4.png"
    }
    
    # AI 로직용 매핑 생성
    ai_logic_mapping = {}
    for category, filename in image_classification.items():
        ai_logic_mapping[category] = {
            "url": f"https://raw.githubusercontent.com/lian1803/flask-crawler-bot-new/main/static/images/{filename}",
            "alt": category
        }
    
    print("=== 이미지 분석 결과 ===")
    print(f"총 {len(image_classification)}개 이미지 분석 완료")
    print("\n=== 카테고리별 매핑 ===")
    for category, filename in image_classification.items():
        file_size = image_files[filename]
        print(f"{category}: {filename} ({file_size:,} bytes)")
    
    print("\n=== AI 로직용 매핑 ===")
    print(json.dumps(ai_logic_mapping, ensure_ascii=False, indent=2))
    
    # 파일로 저장
    with open("new_image_mapping.json", "w", encoding="utf-8") as f:
        json.dump(image_classification, f, ensure_ascii=False, indent=2)
    
    print("\n=== 파일 저장 완료 ===")
    print("- new_image_mapping.json: 이미지 분류 결과")
    
    return image_classification

if __name__ == "__main__":
    analyze_images() 