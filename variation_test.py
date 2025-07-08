import json
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_logic import AILogic
from config import OPENAI_API_KEY, OPENAI_MODEL

import openai
openai.api_key = OPENAI_API_KEY

def load_test_data():
    """테스트 데이터 로드"""
    try:
        with open('school_dataset.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("school_dataset.json 파일을 찾을 수 없습니다.")
        return None

def create_variations(original_question):
    """질문의 변형 버전들을 생성"""
    variations = []
    
    # 1. 오타 변형
    typos = {
        '와석초': ['와석초', '와석초등학교', '와석초등'],
        '급식': ['급식', '급식식단', '급식메뉴'],
        '방과후': ['방과후', '방과후활동', '방과후프로그램'],
        '상담': ['상담', '상담신청', '상담예약'],
        '전학': ['전학', '전학신청', '전학절차'],
        '결석': ['결석', '결석신고', '결석처리'],
        '등하교': ['등하교', '등교', '하교'],
        '학교폭력': ['학교폭력', '폭력', '폭력신고']
    }
    
    # 2. 비슷한 단어/표현
    synonyms = {
        '언제': ['언제', '몇시', '시간', '시각'],
        '어디서': ['어디서', '어디', '장소', '위치'],
        '어떻게': ['어떻게', '방법', '절차', '과정'],
        '신청': ['신청', '신청서', '신청방법', '신청절차'],
        '문의': ['문의', '질문', '상담', '연락'],
        '안내': ['안내', '정보', '소개', '가이드']
    }
    
    # 3. 다른 표현
    expressions = {
        '급식': ['급식', '식단', '점심', '밥', '메뉴'],
        '방과후': ['방과후', '방과후활동', '방과후프로그램', '방과후수업'],
        '상담': ['상담', '상담신청', '상담예약', '상담문의'],
        '공지': ['공지', '공지사항', '알림', '소식', '뉴스']
    }
    
    # 원본 질문을 기반으로 변형 생성
    for category, words in typos.items():
        if category in original_question:
            for word in words:
                if word != category:
                    variation = original_question.replace(category, word)
                    variations.append((f"오타/비슷한단어: {category} → {word}", variation))
    
    for category, words in synonyms.items():
        if category in original_question:
            for word in words:
                if word != category:
                    variation = original_question.replace(category, word)
                    variations.append((f"동의어: {category} → {word}", variation))
    
    for category, words in expressions.items():
        if category in original_question:
            for word in words:
                if word != category:
                    variation = original_question.replace(category, word)
                    variations.append((f"다른표현: {category} → {word}", variation))
    
    # 4. 간단한 오타 (자음/모음 추가/제거)
    simple_typos = [
        ('급식', '급식식'),
        ('방과후', '방과후후'),
        ('상담', '상담담'),
        ('전학', '전학학'),
        ('결석', '결석석'),
        ('등하교', '등하교교')
    ]
    
    for original, typo in simple_typos:
        if original in original_question:
            variation = original_question.replace(original, typo)
            variations.append((f"간단오타: {original} → {typo}", variation))
    
    return variations

def create_more_variations(original_question):
    """더 다양한 변형 버전 생성 (향상된 버전)"""
    variations = set()
    variations.add(original_question)
    
    # 기존 변형
    for v in create_variations(original_question):
        variations.add(v[1])
    
    # 1. 띄어쓰기 변형 (더 스마트하게)
    if ' ' in original_question:
        # 띄어쓰기 제거
        variations.add(original_question.replace(' ', ''))
        # 일부 띄어쓰기만 제거
        words = original_question.split()
        if len(words) > 2:
            variations.add(words[0] + ''.join(words[1:]))
            variations.add(''.join(words[:-1]) + words[-1])
    
    # 2. 단어 생략 (더 정교하게)
    words = original_question.split()
    if len(words) > 2:
        # 첫 단어 제거
        variations.add(' '.join(words[1:]))
        # 마지막 단어 제거
        variations.add(' '.join(words[:-1]))
        # 중간 단어 제거
        if len(words) > 3:
            variations.add(' '.join(words[:2] + words[3:]))
    
    # 3. 오타 시뮬레이션 (더 현실적으로)
    if len(original_question) > 3:
        # 마지막 글자 제거
        variations.add(original_question[:-1])
        # 첫 글자 제거
        variations.add(original_question[1:])
    
    # 4. 자음/모음 추가 (한글 특성 반영)
    if len(original_question) > 2:
        # 중간에 자음 추가
        variations.add(original_question[:2] + 'ㅋ' + original_question[2:])
        # 끝에 자음 추가
        variations.add(original_question + 'ㅋ')
    
    # 5. 문장 부호 변형
    if '?' in original_question:
        variations.add(original_question.replace('?', ''))
        variations.add(original_question.replace('?', '?'))
    if '!' in original_question:
        variations.add(original_question.replace('!', ''))
    
    # 6. 숫자 변형
    for i in range(1, 7):
        if str(i) in original_question:
            variations.add(original_question.replace(str(i), 'X'))
    
    # 7. 특수 패턴 변형
    if 'O학년' in original_question:
        variations.add(original_question.replace('O학년', '1학년'))
        variations.add(original_question.replace('O학년', '3학년'))
        variations.add(original_question.replace('O학년', '6학년'))
    
    if 'oo' in original_question:
        variations.add(original_question.replace('oo', '수학'))
        variations.add(original_question.replace('oo', '영어'))
    
    # 8. 더 짧은 버전들
    if len(words) > 3:
        # 핵심 키워드만 남기기
        key_words = []
        for word in words:
            if any(keyword in word for keyword in ['방과후', '급식', '상담', '전학', '결석', '유치원', '학교']):
                key_words.append(word)
        if key_words:
            variations.add(' '.join(key_words))
    
    return list(variations)

def ask_openai(question):
    try:
        response = openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": question}],
            temperature=0.7,
            max_tokens=150,
            top_p=1.0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[OpenAI 오류] {e}")
        return None

def test_all_variations():
    print("=== 전체 변형+AI 테스트 시작 ===\n")
    ai_logic = AILogic()
    test_data = load_test_data()
    if not test_data:
        return
    total_tests = 0
    keyword_success = 0
    ai_success = 0
    fail = 0
    categories = {}
    for qa in test_data:
        category = qa.get('category', '기타')
        if category not in categories:
            categories[category] = []
        categories[category].append(qa)
    for category, questions in categories.items():
        print(f"\n--- {category} 카테고리 전체 테스트 ---")
        for qa in questions:
            original_question = qa['question']
            original_answer = qa['answer']
            variations = create_more_variations(original_question)
            for variation_question in variations:
                total_tests += 1
                # 1. 키워드 매칭
                success, response = ai_logic.process_message(variation_question, "test_user")
                if success and response:
                    # 유사도 평가
                    original_keywords = set(original_answer.lower().split())
                    response_keywords = set(response.lower().split())
                    common_keywords = original_keywords & response_keywords
                    similarity = len(common_keywords) / max(len(original_keywords), 1)
                    if similarity > 0.15:  # 더 관대한 기준
                        keyword_success += 1
                        print(f"  ✅ 키워드: {variation_question} → {response[:40]} (유사도 {similarity:.2f})")
                        continue
                # 2. AI 호출
                ai_response = ask_openai(variation_question)
                if ai_response:
                    ai_keywords = set(ai_response.lower().split())
                    common_keywords = set(original_answer.lower().split()) & ai_keywords
                    similarity = len(common_keywords) / max(len(set(original_answer.lower().split())), 1)
                    if similarity > 0.15:  # 더 관대한 기준
                        ai_success += 1
                        print(f"  🤖 AI: {variation_question} → {ai_response[:40]} (유사도 {similarity:.2f})")
                        continue
                fail += 1
                print(f"  ❌ 실패: {variation_question}")
                time.sleep(0.5)  # OpenAI API rate limit 방지
    print(f"\n=== 결과 요약 ===")
    print(f"총 테스트: {total_tests}")
    print(f"키워드 매칭 성공: {keyword_success}")
    print(f"AI 매칭 성공: {ai_success}")
    print(f"실패: {fail}")
    print(f"키워드+AI 총 성공률: {((keyword_success+ai_success)/total_tests*100):.1f}%")
    if (keyword_success+ai_success)/total_tests > 0.7:
        print("✅ 전체 매칭 성능이 우수합니다!")
    elif (keyword_success+ai_success)/total_tests > 0.5:
        print("⚠️ 전체 매칭 성능이 보통입니다.")
    else:
        print("❌ 전체 매칭 성능이 개선이 필요합니다.")

if __name__ == "__main__":
    test_all_variations() 