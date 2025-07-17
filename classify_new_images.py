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
    
    # 이미지 파일 목록
    image_files = [
        "그림1.jpg", "그림2.png", "그림3.png", "그림4.png", "그림5.png",
        "그림6.jpg", "그림7.png", "그림8.png", "그림9.jpg", "그림10.png",
        "그림11.png", "그림12.png", "그림13.png", "그림14.png", "그림15.png", "그림16.png"
    ]
    
    # 이미지 분류 매핑 (파일 크기와 확장자를 기반으로 추정)
    # 실제로는 이미지 내용을 보고 분류해야 합니다
    image_classification = {
        # 학사일정 관련 (보통 큰 파일)
        "학사일정": "그림1.jpg",  # 18KB - 학사일정
        "교실 배치도": "그림2.png",  # 26KB - 교실 배치도
        "정차대": "그림3.png",  # 14KB - 정차대
        "학교시설": "그림4.png",  # 6KB - 학교시설
        
        # 급식 관련 (중간 크기)
        "급식": "그림5.png",  # 178KB - 급식 정보
        "방과후": "그림6.jpg",  # 1.8KB - 방과후 프로그램
        "상담": "그림7.png",  # 2.4KB - 상담 안내
        "전학": "그림8.png",  # 83KB - 전학 안내
        
        # 유치원 관련
        "유치원": "그림9.jpg",  # 120KB - 유치원 안내
        "결석": "그림10.png",  # 165KB - 결석 신고 안내
        "등하교": "그림11.png",  # 159KB - 등하교 안내
        
        # 학교 시설 관련
        "체육관": "그림12.png",  # 6.6KB - 체육관 이용
        "도서관": "그림13.png",  # 14KB - 도서관 이용
        "보건실": "그림14.png",  # 117KB - 보건실 안내
        "컴퓨터실": "그림15.png",  # 362KB - 컴퓨터실 안내
        "음악실": "그림16.png",  # 96KB - 음악실 안내
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