import json
from datetime import datetime

def get_base_message(user_id: str, text: str):
    """카카오톡 응답 메시지 기본 형식을 생성합니다."""
    return {
        "user_id": user_id,
        "message": {
            "text": text,
            "quick_replies": []
        }
    }

def get_quick_reply(action_type: str, label: str, message: str):
    """퀵리플라이 버튼을 생성합니다."""
    return {
        "action": action_type,
        "label": label,
        "messageText": message
    }

def create_kakao_response(message: str, quick_replies=None):
    """카카오톡 챗봇 응답 형식을 생성합니다."""
    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": message
                    }
                }
            ]
        }
    }
    
    if quick_replies:
        response["template"]["quickReplies"] = quick_replies
    
    return response

def format_meal_info(meal_data: dict):
    """급식 정보를 포맷팅합니다."""
    if not meal_data:
        return "급식 정보를 찾을 수 없습니다."
    
    formatted = f"📅 {meal_data['date']} 중식\n\n"
    formatted += meal_data['menu']
    
    return formatted

def format_notice_info(notices: list):
    """공지사항 정보를 포맷팅합니다."""
    if not notices:
        return "최신 공지사항이 없습니다."
    
    formatted = "📢 최신 공지사항\n\n"
    for i, notice in enumerate(notices[:5], 1):
        formatted += f"{i}. {notice['title']}\n"
        if notice.get('created_at'):
            formatted += f"   📅 {notice['created_at']}\n"
        formatted += "\n"
    
    return formatted

def extract_date_from_text(text: str):
    """텍스트에서 날짜를 추출합니다."""
    import re
    from datetime import datetime, timedelta
    
    today = datetime.now()
    
    if "오늘" in text:
        return today.strftime("%Y-%m-%d")
    elif "내일" in text:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    elif "어제" in text:
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    elif "모레" in text:
        return (today + timedelta(days=2)).strftime("%Y-%m-%d")
    
    # "5월 20일", "5/20" 같은 패턴 찾기
    match = re.search(r'(\d{1,2})[월/\s](\d{1,2})일?', text)
    if match:
        month, day = map(int, match.groups())
        return today.replace(month=month, day=day).strftime("%Y-%m-%d")
    
    return None

def is_meal_related(text: str):
    """급식 관련 키워드인지 확인합니다."""
    meal_keywords = [
        "급식", "식단", "메뉴", "점심", "중식", "아침", "조식", "저녁", "석식",
        "오늘 급식", "오늘 식단", "오늘 메뉴", "내일 급식", "내일 식단"
    ]
    return any(keyword in text for keyword in meal_keywords)

def is_notice_related(text: str):
    """공지사항 관련 키워드인지 확인합니다."""
    notice_keywords = [
        "공지", "공지사항", "알림", "안내", "새소식", "뉴스", "소식"
    ]
    return any(keyword in text for keyword in notice_keywords)

def is_greeting(text: str):
    """인사말인지 확인합니다."""
    greetings = [
        "안녕", "하이", "반가워", "안녕하세요", "안녕하십니까",
        "좋은 아침", "좋은 하루", "좋은 저녁"
    ]
    return any(greeting in text for greeting in greetings) 