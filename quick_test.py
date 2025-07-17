#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ai_logic import AILogic

def test_improved_logic():
    ai = AILogic()
    
    print("=== 학교 관련성 판별 테스트 ===")
    test_cases = [
        '개학일', '개학 날짜', '안녕', '도움', '감사', '날씨', '바보',
        '급식', '방과후', '전학', '상담', '결석', '교실', '등하교'
    ]
    
    for case in test_cases:
        result = ai.is_school_related(case)
        print(f"{case}: {result}")
    
    print("\n=== 간단한 응답 테스트 ===")
    simple_cases = ['안녕', '도움', '감사', '고마워', '뭐해', '잘 있어']
    
    for case in simple_cases:
        success, response = ai.process_message(case, "test_user")
        print(f"{case}: {response}")
    
    print("\n=== QA 매칭 테스트 ===")
    qa_cases = [
        '개학 언제야', '학교 전화번호', '급식 메뉴', '방과후 시간',
        '전학 절차', '상담 신청', '결석 신고'
    ]
    
    for case in qa_cases:
        qa_match = ai.find_qa_match(case)
        if qa_match:
            print(f"{case}: {qa_match['question']} -> {qa_match['answer']}")
        else:
            print(f"{case}: 매칭 없음")

if __name__ == "__main__":
    test_improved_logic() 