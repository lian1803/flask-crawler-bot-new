# 와석초등학교 카카오톡 챗봇 (개선판)

기존 `rol` 폴더의 챗봇을 `temp_machaao`의 로직을 참고하여 개선한 버전입니다.

## 🚀 주요 개선사항

### 1. **AI 로직 개선**
- OpenAI GPT 통합으로 더 자연스러운 대화
- 대화 히스토리 기반 컨텍스트 유지
- TF-IDF 기반 유사도 매칭으로 정확한 QA 응답

### 2. **코드 구조 개선**
- 모듈화된 구조 (config, database, ai_logic 분리)
- 깔끔한 예외 처리
- 타입 힌팅 적용

### 3. **기능 강화**
- 대화 히스토리 저장 및 관리
- 금지 단어 필터링
- 퀵 리플라이 버튼 지원
- 헬스 체크 및 통계 엔드포인트

## 📁 파일 구조

```
new/
├── app.py              # 메인 Flask 애플리케이션
├── config.py           # 환경 설정
├── database.py         # 데이터베이스 관리
├── ai_logic.py         # AI 처리 로직
├── data_migration.py   # 데이터 마이그레이션
├── requirements.txt    # 의존성 목록
├── README.md          # 프로젝트 설명
└── school_data.db     # 데이터베이스 (마이그레이션 후 생성)
```

## 🛠️ 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가:
```env
OPENAI_API_KEY=your_openai_api_key
KAKAO_API_KEY=your_kakao_api_key
KAKAO_BOT_TOKEN=your_kakao_bot_token
PORT=5000
DEBUG=True
TEMPERATURE=0.7
MAX_TOKENS=150
```

### 3. 데이터 마이그레이션
```bash
python data_migration.py
```

### 4. 서버 실행
```bash
python app.py
```

## 🔧 API 엔드포인트

### 카카오톡 웹훅
- `POST /webhook` - 카카오톡 메시지 처리

### 테스트 및 관리
- `GET /` - 서버 상태 확인
- `GET /health` - 헬스 체크
- `GET /stats` - 통계 정보
- `GET/POST /test` - 테스트 엔드포인트

## 🧠 AI 처리 로직

1. **금지 단어 필터링** - 부적절한 내용 차단
2. **식단 정보 조회** - 급식 메뉴 관련 질문 처리
3. **공지사항 조회** - 학교 공지사항 관련 질문 처리
4. **QA 데이터베이스 매칭** - TF-IDF 유사도 기반 정확한 답변
5. **OpenAI GPT 응답** - 일반적인 대화 및 복잡한 질문 처리

## 📊 데이터베이스 구조

- `qa_data` - 질문과 답변 데이터
- `conversation_history` - 대화 히스토리
- `meals` - 식단 정보
- `notices` - 공지사항

## 🔄 기존 시스템과의 차이점

| 구분 | 기존 (rol) | 개선판 (new) |
|------|------------|--------------|
| AI 엔진 | 복잡한 규칙 기반 | OpenAI GPT + TF-IDF |
| 대화 관리 | 세션 기반 | 히스토리 기반 |
| 코드 구조 | 단일 파일 | 모듈화 |
| 에러 처리 | 기본적 | 체계적 |
| 확장성 | 제한적 | 높음 |

## 🚀 배포

### 로컬 테스트
```bash
curl -X POST http://localhost:5000/test \
  -H "Content-Type: application/json" \
  -d '{"message": "오늘 급식 메뉴 알려줘", "user_id": "test_user"}'
```

### 카카오톡 연동
웹훅 URL: `https://your-domain.com/webhook`

## 📝 참고 자료

- 기존 챗봇: `../rol/`
- 참고 템플릿: `../Temp/temp_machaao/`
- 학교 데이터: `와석초 카카오톡 챗봇 개발을 위한 질문과 답변 의 사본.xlsx` 