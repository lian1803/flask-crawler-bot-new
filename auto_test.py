import requests
import json
import time

def test_webhook(message):
    """웹훅 엔드포인트 테스트"""
    url = "http://localhost:5000/webhook"
    
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
            print(f"\n=== 테스트: '{message}' ===")
            
            # 응답 내용 파싱
            if 'template' in result and 'outputs' in result['template']:
                for output in result['template']['outputs']:
                    if 'simpleText' in output:
                        text = output['simpleText']['text']
                        print(f"답변: {text}")
                        
                        # 문제점 체크
                        if len(text) < 10:
                            print("⚠️  문제: 답변이 너무 짧음")
                        if "이미지 파일 첨부" in text or "이미지 파일 참조" in text:
                            print("⚠️  문제: 이미지 링크가 제대로 처리되지 않음")
                        if "https://" in text:
                            print("✅ 이미지 링크 포함됨")
            
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
            print(f"❌ 오류: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        return None

def run_all_tests():
    """모든 테스트 자동 실행"""
    print("🚀 와석초 챗봇 자동 테스트 시작\n")
    
    # 1. 기본 인사 테스트
    print("📋 1단계: 기본 인사 테스트")
    test_webhook("안녕하세요")
    test_webhook("안녕")
    test_webhook("도움")
    time.sleep(1)
    
    # 2. 메뉴 구조 테스트
    print("\n📋 2단계: 메뉴 구조 테스트")
    test_webhook("유치원")
    test_webhook("초등학교")
    test_webhook("메인메뉴")
    time.sleep(1)
    
    # 3. 유치원 세부 메뉴 테스트
    print("\n📋 3단계: 유치원 세부 메뉴 테스트")
    test_webhook("유치원 학사일정")
    test_webhook("유치원 운영시간")
    test_webhook("유치원 방과후")
    test_webhook("유치원 상담문의")
    time.sleep(1)
    
    # 4. 초등학교 세부 메뉴 테스트
    print("\n📋 4단계: 초등학교 세부 메뉴 테스트")
    test_webhook("학사일정")
    test_webhook("급식정보")
    test_webhook("방과후")
    test_webhook("상담문의")
    test_webhook("더보기")
    time.sleep(1)
    
    # 5. 실제 질문 테스트 (이미지 포함)
    print("\n📋 5단계: 실제 질문 테스트 (이미지 포함)")
    test_webhook("유치원 운영 시간을 알고 싶어요")
    test_webhook("유치원 교육비는 얼마인가요")
    test_webhook("오늘의 급식은?")
    test_webhook("학교 전화번호")
    test_webhook("방과후 언제 끝나?")
    test_webhook("유치원 담임 선생님 연락처")
    time.sleep(1)
    
    # 6. 이미지 관련 질문 테스트
    print("\n📋 6단계: 이미지 관련 질문 테스트")
    test_webhook("학사일정")
    test_webhook("교실 배치도")
    test_webhook("정차대 위치")
    test_webhook("학교시설 이용")
    test_webhook("방과후 강좌")
    time.sleep(1)
    
    # 7. 특수 케이스 테스트
    print("\n📋 7단계: 특수 케이스 테스트")
    test_webhook("유치원 개학일")
    test_webhook("유치원 방학일")
    test_webhook("유치원 졸업식")
    test_webhook("개학일")
    test_webhook("방학일")
    test_webhook("시험일")
    time.sleep(1)
    
    # 8. 급식 관련 테스트
    print("\n📋 8단계: 급식 관련 테스트")
    test_webhook("오늘 급식 메뉴 알려줘")
    test_webhook("이번주 급식 메뉴 알려줘")
    test_webhook("급식 관련 문의")
    test_webhook("급식 알레르기 정보")
    time.sleep(1)
    
    # 9. 방과후 관련 테스트
    print("\n📋 9단계: 방과후 관련 테스트")
    test_webhook("늘봄교실")
    test_webhook("방과후학교")
    test_webhook("방과후 신청방법")
    test_webhook("방과후 운영시간")
    time.sleep(1)
    
    # 10. 상담 관련 테스트
    print("\n📋 10단계: 상담 관련 테스트")
    test_webhook("담임선생님 상담")
    test_webhook("학교 전화번호")
    test_webhook("전학 문의")
    test_webhook("서류 발급 문의")
    time.sleep(1)
    
    # 11. 기타 테스트
    print("\n📋 11단계: 기타 테스트")
    test_webhook("학교시설")
    test_webhook("등하교")
    test_webhook("보건실")
    test_webhook("감사합니다")
    test_webhook("고마워")
    time.sleep(1)
    
    print("\n🎉 모든 테스트 완료!")

if __name__ == "__main__":
    run_all_tests() 