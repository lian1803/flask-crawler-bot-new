import json
import sys
import traceback
import jwt
import requests
from datetime import datetime
from dotenv import load_dotenv

# Flask 및 기타 라이브러리
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# 로컬 모듈
from config import api_token, open_api_key, base_url, dashbot_key, dashbot_url, port
from logic.bot_logic import SchoolBotLogic
from database import SchoolDatabase
from utils import create_kakao_response, get_quick_reply

load_dotenv()

app = Flask(__name__)

# 스케줄러 초기화
scheduler = BackgroundScheduler()
scheduler.start()

# 봇 로직 및 데이터베이스 초기화
bot_logic = SchoolBotLogic()
db = SchoolDatabase()

# 대시보드 설정 확인
if not dashbot_key:
    print("Dashbot key not present in env. Disabling dashbot logging")

def exception_handler(exception):
    """예외 처리를 위한 헬퍼 함수"""
    caller = sys._getframe(1).f_code.co_name
    print(f"{caller} function failed")
    if hasattr(exception, "message"):
        print(exception.message)
    else:
        print("Unexpected error: ", sys.exc_info()[0])

def extract_sender(req):
    """요청에서 사용자 ID를 추출합니다."""
    try:
        return req.headers["machaao-user-id"]
    except Exception as e:
        exception_handler(e)
        return "unknown_user"

def extract_message(req):
    """요청에서 메시지를 추출합니다."""
    try:
        decoded_jwt = None
        body = req.json
        if body and body["raw"]:
            decoded_jwt = jwt.decode(body["raw"], api_token, algorithms=["HS512"])
        
        text = decoded_jwt["sub"]
        if type(text) == str:
            text = json.loads(decoded_jwt["sub"])

        sdk = text["messaging"][0]["version"]
        sdk = sdk.replace("v", "")
        client = text["messaging"][0]["client"]

        try:
            action_type = text["messaging"][0]["message_data"]["action_type"]
        except Exception as e:
            action_type = "text"
            exception_handler(e)

        return (
            text["messaging"][0]["message_data"]["text"],
            text["messaging"][0]["message_data"]["label"],
            client,
            sdk,
            action_type,
        )
    except Exception as e:
        exception_handler(e)
        return ("", "", "web", "1.0", "text")

def send_reply(valid: bool, text: str, user_id: str, client: str, sdk: float):
    """응답을 전송합니다."""
    try:
        # 카카오톡 응답 형식 생성
        response = create_kakao_response(text)
        
        # 퀵리플라이 추가
        if valid and client != "web":
            response["template"]["quickReplies"] = [
                get_quick_reply("text", "오늘 급식", "오늘 급식"),
                get_quick_reply("text", "공지사항", "공지사항"),
                get_quick_reply("text", "도움말", "도움말")
            ]

        # 대시보드 로깅
        if dashbot_key:
            send_to_dashbot(text=text, user_id=user_id, msg_type="send")

        return response

    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        exception_handler(e)
        return create_kakao_response("죄송합니다. 오류가 발생했습니다.")

def send_to_dashbot(text, user_id, msg_type):
    """대시보드에 로그를 전송합니다."""
    try:
        payload = {
            "text": text,
            "userId": user_id,
        }

        if msg_type == "recv":
            url = dashbot_url.format(type="incoming", apiKey=dashbot_key)
        else:
            url = dashbot_url.format(type="outgoing", apiKey=dashbot_key)

        header = {"Content-Type": "application/json"}
        requests.post(url=url, data=json.dumps(payload), headers=header)

    except Exception as e:
        exception_handler(e)

def auto_update_excel_data():
    """매일 자정에 실행되는 엑셀 데이터 자동 업데이트"""
    try:
        print(f"[{datetime.now()}] 엑셀 데이터 자동 업데이트 시작")
        success = db.update_excel_data()
        if success:
            print(f"[{datetime.now()}] 엑셀 데이터 자동 업데이트 완료")
        else:
            print(f"[{datetime.now()}] 엑셀 데이터 업데이트 실패")
    except Exception as e:
        print(f"[{datetime.now()}] 엑셀 데이터 자동 업데이트 중 오류: {str(e)}")

# 스케줄러에 작업 추가 (매일 자정에 실행)
scheduler.add_job(
    func=auto_update_excel_data,
    trigger=CronTrigger(hour=0, minute=0),
    id='auto_update_excel_data',
    name='엑셀 데이터 자동 업데이트',
    replace_existing=True
)

print(f"[{datetime.now()}] 스케줄러가 시작되었습니다. 매일 자정에 엑셀 데이터가 자동으로 업데이트됩니다.")

@app.route("/", methods=["GET"])
def root():
    """루트 엔드포인트"""
    return "파주와석초등학교 챗봇 서버 v3.0 (AI 기반 개선)"

@app.route("/machaao/hook", methods=["GET", "POST"])
@app.route("/webhooks/machaao/incoming", methods=["GET", "POST"])
def receive():
    """Machaao 플랫폼 웹훅 처리"""
    return process_response(request)

@app.route("/webhook", methods=["POST"])
def kakao_webhook():
    """카카오톡 챗봇 웹훅 처리"""
    try:
        data = request.get_json()
        user_message = data['userRequest']['utterance']
        user_id = data['userRequest']['user']['id']
        
        # 봇 로직으로 메시지 처리
        response_text = bot_logic.process_message(user_message, user_id)
        
        print(f"사용자: '{user_message}' / 챗봇: '{response_text[:50]}...'")
        return jsonify(create_kakao_response(response_text))
        
    except Exception as e:
        print(f"카카오톡 웹훅 오류: {str(e)}")
        return jsonify(create_kakao_response("시스템에 오류가 발생하여 요청을 처리할 수 없습니다."))

def process_response(request):
    """Machaao 플랫폼 응답 처리"""
    try:
        _api_token = request.headers["bot-token"]
        sender_id = extract_sender(request)
        recv_text, label, client, sdk, action_type = extract_message(request)

        if dashbot_key:
            send_to_dashbot(text=recv_text, user_id=sender_id, msg_type="recv")

        # 봇 로직으로 메시지 처리
        response_text = bot_logic.process_message(recv_text, sender_id)
        
        # 응답 전송
        response = send_reply(True, response_text, sender_id, client, float(sdk))
        
        return jsonify(response)

    except Exception as e:
        print(f"응답 처리 중 오류: {str(e)}")
        return jsonify(create_kakao_response("죄송합니다. 오류가 발생했습니다."))

@app.route('/test')
def test_page():
    """테스트용 HTML 페이지"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>와석초 챗봇 테스트</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .button { 
                background: #007bff; color: white; padding: 10px 20px; 
                border: none; border-radius: 5px; cursor: pointer; margin: 5px;
                transition: background 0.3s;
            }
            .button:hover { background: #0056b3; }
            .result { 
                background: #f8f9fa; border: 1px solid #dee2e6; 
                border-radius: 5px; padding: 15px; margin: 10px 0;
                white-space: pre-wrap; font-family: monospace; max-height: 300px; overflow-y: auto;
            }
            .success { border-color: #28a745; background: #d4edda; }
            .error { border-color: #dc3545; background: #f8d7da; }
            .chat-test { margin: 20px 0; }
            .chat-input { width: 70%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            .chat-send { padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; }
            .chat-messages { margin: 10px 0; max-height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; background: #f9f9f9; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏫 파주와석초등학교 챗봇 테스트</h1>
            
            <h2>1. 시스템 상태 확인</h2>
            <button class="button" onclick="checkSystem()">시스템 상태 확인</button>
            <div id="systemResult" class="result"></div>
            
            <h2>2. 데이터베이스 상태</h2>
            <button class="button" onclick="checkDB()">DB 상태 확인</button>
            <div id="dbResult" class="result"></div>
            
            <h2>3. 엑셀 데이터 업데이트</h2>
            <button class="button" onclick="updateExcel()">엑셀 데이터 업데이트</button>
            <div id="excelResult" class="result"></div>
            
            <h2>4. 챗봇 테스트</h2>
            <div class="chat-test">
                <input type="text" id="chatInput" class="chat-input" placeholder="메시지를 입력하세요..." onkeypress="if(event.keyCode==13) sendMessage()">
                <button class="chat-send" onclick="sendMessage()">전송</button>
            </div>
            <div id="chatMessages" class="chat-messages"></div>
        </div>
        
        <script>
            async function checkSystem() {
                try {
                    const response = await fetch('/system-status');
                    const data = await response.json();
                    document.getElementById('systemResult').innerHTML = JSON.stringify(data, null, 2);
                    document.getElementById('systemResult').className = 'result success';
                } catch (error) {
                    document.getElementById('systemResult').innerHTML = '오류: ' + error.message;
                    document.getElementById('systemResult').className = 'result error';
                }
            }
            
            async function checkDB() {
                try {
                    const response = await fetch('/db-status');
                    const data = await response.json();
                    document.getElementById('dbResult').innerHTML = JSON.stringify(data, null, 2);
                    document.getElementById('dbResult').className = 'result success';
                } catch (error) {
                    document.getElementById('dbResult').innerHTML = '오류: ' + error.message;
                    document.getElementById('dbResult').className = 'result error';
                }
            }
            
            async function updateExcel() {
                try {
                    document.getElementById('excelResult').innerHTML = '업데이트 중...';
                    const response = await fetch('/update-excel', {method: 'POST'});
                    const data = await response.json();
                    document.getElementById('excelResult').innerHTML = JSON.stringify(data, null, 2);
                    document.getElementById('excelResult').className = 'result success';
                } catch (error) {
                    document.getElementById('excelResult').innerHTML = '오류: ' + error.message;
                    document.getElementById('excelResult').className = 'result error';
                }
            }
            
            async function sendMessage() {
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                if (!message) return;
                
                const messagesDiv = document.getElementById('chatMessages');
                messagesDiv.innerHTML += '<div><strong>사용자:</strong> ' + message + '</div>';
                
                try {
                    const response = await fetch('/test-chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({message: message, user_id: 'test_user'})
                    });
                    const data = await response.json();
                    messagesDiv.innerHTML += '<div><strong>챗봇:</strong> ' + data.response + '</div>';
                } catch (error) {
                    messagesDiv.innerHTML += '<div><strong>오류:</strong> ' + error.message + '</div>';
                }
                
                input.value = '';
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    return html

@app.route('/system-status', methods=['GET'])
def get_system_status():
    """시스템 상태를 확인합니다."""
    try:
        jobs = scheduler.get_jobs()
        job_info = []
        for job in jobs:
            job_info.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else "None"
            })
        
        return jsonify({
            "status": "running",
            "scheduler_jobs": job_info,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/db-status', methods=['GET'])
def get_db_status():
    """데이터베이스 상태를 확인합니다."""
    try:
        status = db.get_db_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/update-excel', methods=['POST'])
def manual_update_excel():
    """수동으로 엑셀 데이터 업데이트를 실행합니다."""
    try:
        print(f"[{datetime.now()}] 수동 엑셀 데이터 업데이트 요청됨")
        success = db.update_excel_data()
        
        if success:
            return jsonify({
                "status": "success",
                "message": "엑셀 데이터 업데이트가 완료되었습니다.",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "엑셀 데이터 업데이트에 실패했습니다.",
                "timestamp": datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        print(f"[{datetime.now()}] 수동 업데이트 중 오류: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"업데이트 중 오류가 발생했습니다: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/test-chat', methods=['POST'])
def test_chat():
    """챗봇 테스트용 엔드포인트"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        user_id = data.get('user_id', 'test_user')
        
        if not user_message:
            return jsonify({"error": "메시지가 없습니다."}), 400
        
        response = bot_logic.process_message(user_message, user_id)
        return jsonify({"response": response})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=port) 