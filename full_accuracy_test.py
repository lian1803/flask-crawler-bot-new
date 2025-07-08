import json
from simple_keyword_chatbot import SimpleKeywordChatbot

def test_all_questions():
    """모든 질문에 대한 정확도 테스트"""
    chatbot = SimpleKeywordChatbot()
    
    # 모든 질문 로드
    with open('school_dataset.json', 'r', encoding='utf-8') as f:
        all_qa_data = json.load(f)
    
    print(f"=== 전체 질문 정확도 테스트 ===\n")
    print(f"총 질문 수: {len(all_qa_data)}개\n")
    
    # 각 질문을 자기 자신과 매칭 테스트
    correct_matches = 0
    total_questions = len(all_qa_data)
    
    for i, qa in enumerate(all_qa_data, 1):
        original_question = qa['question']
        original_answer = qa['answer']
        
        # 자기 자신과 매칭 테스트
        response, confidence = chatbot.find_similar_question(original_question)
        
        # 정확도 판단 (자기 자신과 매칭되어야 함)
        is_correct = confidence >= 0.3
        
        if is_correct:
            correct_matches += 1
            status = "✅ 매칭"
        else:
            status = "❌ 실패"
        
        print(f"{i:2d}. 질문: {original_question}")
        print(f"    답변: {original_answer[:50]}...")
        print(f"    매칭 점수: {confidence:.2f}")
        print(f"    결과: {status}")
        print("-" * 80)
    
    accuracy = (correct_matches / total_questions) * 100
    print(f"\n=== 전체 정확도 결과 ===")
    print(f"총 질문: {total_questions}개")
    print(f"성공한 매칭: {correct_matches}개")
    print(f"실패한 매칭: {total_questions - correct_matches}개")
    print(f"정확도: {accuracy:.1f}%")
    
    # 카테고리별 분석
    print(f"\n=== 카테고리별 분석 ===")
    categories = {}
    for qa in all_qa_data:
        cat = qa['category']
        if cat not in categories:
            categories[cat] = {'total': 0, 'success': 0}
        categories[cat]['total'] += 1
    
    # 각 카테고리별로 다시 테스트
    for cat in categories:
        cat_questions = [qa for qa in all_qa_data if qa['category'] == cat]
        cat_success = 0
        
        for qa in cat_questions:
            response, confidence = chatbot.find_similar_question(qa['question'])
            if confidence >= 0.3:
                cat_success += 1
        
        categories[cat]['success'] = cat_success
        cat_accuracy = (cat_success / categories[cat]['total']) * 100
        print(f"{cat}: {cat_success}/{categories[cat]['total']} ({cat_accuracy:.1f}%)")
    
    # 매칭 점수 분포 분석
    print(f"\n=== 매칭 점수 분포 ===")
    score_ranges = {
        "0.0-0.5": 0,
        "0.5-1.0": 0,
        "1.0-1.5": 0,
        "1.5-2.0": 0,
        "2.0+": 0
    }
    
    for qa in all_qa_data:
        response, confidence = chatbot.find_similar_question(qa['question'])
        if confidence < 0.5:
            score_ranges["0.0-0.5"] += 1
        elif confidence < 1.0:
            score_ranges["0.5-1.0"] += 1
        elif confidence < 1.5:
            score_ranges["1.0-1.5"] += 1
        elif confidence < 2.0:
            score_ranges["1.5-2.0"] += 1
        else:
            score_ranges["2.0+"] += 1
    
    for range_name, count in score_ranges.items():
        percentage = (count / total_questions) * 100
        print(f"{range_name}: {count}개 ({percentage:.1f}%)")

if __name__ == "__main__":
    test_all_questions() 