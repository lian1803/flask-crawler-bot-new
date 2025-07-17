#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
실제 챗봇 응답에서 이미지가 제대로 표시되는지 테스트하는 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_logic import AILogic

def test_image_responses():
    """이미지가 포함된 응답들을 테스트"""
    
    ai_logic = AILogic()
    
    # 이미지가 포함된 질문들
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
    
    print("=== 이미지 응답 테스트 ===")
    
    for question in test_questions:
        print(f"\n질문: {question}")
        
        try:
            success, response = ai_logic.process_message(question, "test_user")
            
            if success:
                if isinstance(response, dict) and "text" in response:
                    text = response["text"]
                    if "📎 이미지 링크:" in text:
                        print("✅ 이미지 링크 포함됨")
                        # 이미지 링크 추출
                        lines = text.split('\n')
                        for line in lines:
                            if "📎 이미지 링크:" in line:
                                image_url = line.replace("📎 이미지 링크:", "").strip()
                                print(f"   이미지: {image_url}")
                    else:
                        print("❌ 이미지 링크 없음")
                else:
                    print("❌ 응답 형식 오류")
            else:
                print("❌ 처리 실패")
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
    
    print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    test_image_responses() 