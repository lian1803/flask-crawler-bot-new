import json

def simple_chatbot_test():
    # JSON 파일 읽기
    with open('school_dataset.json', 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
    
    print(f"총 {len(qa_data)}개의 Q&A 데이터가 있습니다.")
    print("\n=== 샘플 데이터 ===")
    for i, qa in enumerate(qa_data[:5]):
        print(f"{i+1}. 질문: {qa['question']}")
        print(f"   답변: {qa['answer']}")
        print(f"   카테고리: {qa['category']}")
        print()
    
    # 간단한 키워드 검색 테스트
    print("=== 키워드 검색 테스트 ===")
    test_keywords = ['방과후', '급식', '상담']
    
    for keyword in test_keywords:
        matches = [qa for qa in qa_data if keyword in qa['question']]
        print(f"'{keyword}' 관련 질문: {len(matches)}개")
        if matches:
            print(f"  예시: {matches[0]['question']}")
        print()

if __name__ == "__main__":
    simple_chatbot_test() 