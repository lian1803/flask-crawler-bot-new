import os
from dotenv import load_dotenv

load_dotenv()

# API 설정
api_token = os.environ.get("API_TOKEN", "")
open_api_key = os.environ.get("OPENAI_API_KEY", "")
base_url = os.environ.get("BASE_URL", "https://ganglia.machaao.com")

# 대시보드 설정 (선택사항)
dashbot_key = os.environ.get("DASHBOT_KEY", "")
dashbot_url = "https://tracker.dashbot.io/track?platform=generic&v=11.1.0-rest&type={type}&apiKey={apiKey}"

# 서버 설정
port = int(os.environ.get("PORT", 5000))

# 봇 설정
bot_name = os.environ.get("BOT_NAME", "와석초 챗봇")
bot_personality = os.environ.get("BOT_PERSONALITY", "친근하고 도움이 되는 학교 챗봇")

# AI 모델 설정
openai_model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
temperature = float(os.environ.get("TEMPERATURE", 0.7))
max_tokens = int(os.environ.get("MAX_TOKENS", 150))

# 데이터베이스 설정
db_path = os.environ.get("DB_PATH", "school_data.db")
excel_file = os.environ.get("EXCEL_FILE", "와석초 카카오톡 챗봇 개발을 위한 질문과 답변 의 사본.xlsx") 