import jieba
import json
import numpy as np
from collections import Counter

def debug_test():
    # 데이터 로드
    with open('school_dataset.json', 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
    
    print(f"총 {len(qa_data)}개의 Q&A 데이터")
    
    # 첫 번째 질문 확인
    first_qa = qa_data[0]
    print(f"\n첫 번째 질문: {first_qa['question']}")
    
    # 토크나이징 테스트
    tokens = jieba.lcut(first_qa['question'])
    print(f"토크나이징 결과: {tokens}")
    
    # 유사한 질문 찾기
    test_question = "담임선생님과 상담은 어떻게 할 수 있나요?"
    print(f"\n테스트 질문: {test_question}")
    test_tokens = jieba.lcut(test_question)
    print(f"테스트 토크나이징: {test_tokens}")
    
    # 데이터에서 유사한 질문 찾기
    for i, qa in enumerate(qa_data):
        if "상담" in qa['question']:
            print(f"\n상담 관련 질문 {i}: {qa['question']}")
            qa_tokens = jieba.lcut(qa['question'])
            print(f"토크나이징: {qa_tokens}")
            
            # 공통 토큰 찾기
            common = set(test_tokens) & set(qa_tokens)
            print(f"공통 토큰: {common}")
            break

if __name__ == "__main__":
    debug_test() 