import requests
import json

def test_webhook(message):
    """웹훅 엔드포인트 테스트"""
    url = "http://localhost:5000/webhook"
    
    # 카카오톡 챗봇 형식으로 요청 데이터 구성
    data = {
        "version": "2.0",
        "action": {
            "params": {
                "utterance": message
            }
        },
        "userRequest": {
            "user": {
                "id": "test_user_123"
            },
            "utterance": message
        }
    }
    
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        if response.status_code == 200:
            result = response.json()
            print(f"\n=== 테스트 메시지: '{message}' ===")
            print(f"응답 상태: {response.status_code}")
            
            # 응답 내용 파싱
            if 'template' in result and 'outputs' in result['template']:
                for output in result['template']['outputs']:
                    if 'simpleText' in output:
                        print(f"텍스트 응답: {output['simpleText']['text']}")
            
            # QuickReplies 확인
            if 'template' in result and 'quickReplies' in result['template']:
                print("QuickReplies:")
                for i, reply in enumerate(result['template']['quickReplies'], 1):
                    print(f"  {i}. {reply['label']} -> {reply['messageText']}")
            else:
                print("QuickReplies 없음")
            
            print("-" * 50)
            return result
        else:
            print(f"오류: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
        return None

def test_menu_flow():
    """메뉴 플로우 테스트"""
    print("=== 와석초 챗봇 메뉴 구조 테스트 ===\n")
    
    # 테스트 시나리오
    test_scenarios = [
        "안녕하세요",
        "유치원",
        "유치원 학사일정", 
        "유치원 개학일",
        "유치원",
        "유치원 운영시간",
        "유치원 교육과정 시간",
        "초등학교",
        "급식정보",
        "오늘 급식 메뉴 알려줘",
        "메인메뉴"
    ]
    
    for message in test_scenarios:
        test_webhook(message)
        input("다음 테스트를 위해 Enter를 누르세요...")

def test_specific_questions():
    """특정 질문들 테스트"""
    print("=== 특정 질문 테스트 ===\n")
    
    questions = [
        "유치원 운영 시간을 알고 싶어요",
        "유치원 교육비는 얼마인가요",
        "오늘의 급식은?",
        "학교 전화번호",
        "방과후 언제 끝나?",
        "유치원 담임 선생님 연락처"
    ]
    
    for question in questions:
        test_webhook(question)
        input("다음 질문을 위해 Enter를 누르세요...")

if __name__ == "__main__":
    print("테스트를 선택하세요:")
    print("1. 메뉴 플로우 테스트")
    print("2. 특정 질문 테스트")
    
    choice = input("선택 (1 또는 2): ")
    
    if choice == "1":
        test_menu_flow()
    elif choice == "2":
        test_specific_questions()
    else:
        print("잘못된 선택입니다.") 