from database import DatabaseManager
from template1_ai_based_chatbot import AIBasedChatbot
from template2_qa_chatbot import QAChatbot
from ai_logic import AILogic
import time

# 1. DB에서 모든 질문-정답 쌍 추출
db = DatabaseManager()
qa_list = db.get_qa_data()

# 2. 챗봇 인스턴스
ai_based = AIBasedChatbot()
tfidf_based = QAChatbot()
gpt_based = AILogic()

results = []

print(f"총 {len(qa_list)}개 질문 자동 테스트 시작!")

for i, qa in enumerate(qa_list, 1):
    question = qa['question']  # 반드시 question 컬럼 사용!
    gt_answer = qa['answer']   # 반드시 answer 컬럼 사용!
    row = {'질문': question, '정답': gt_answer}

    # AI-based
    t0 = time.time()
    ai_ans = ai_based.get_response(question)
    t1 = time.time()
    row['AI-based 답변'] = ai_ans
    row['AI-based 시간'] = round(t1-t0, 3)
    row['AI-based 정답여부'] = gt_answer.strip() in ai_ans

    # TF-IDF
    t0 = time.time()
    tfidf_ans = tfidf_based.get_response(question)
    t1 = time.time()
    row['TF-IDF 답변'] = tfidf_ans
    row['TF-IDF 시간'] = round(t1-t0, 3)
    row['TF-IDF 정답여부'] = gt_answer.strip() in tfidf_ans

    # OpenAI GPT
    t0 = time.time()
    _, gpt_ans = gpt_based.process_message(question, "test_user")
    t1 = time.time()
    row['GPT 답변'] = gpt_ans
    row['GPT 시간'] = round(t1-t0, 3)
    row['GPT 정답여부'] = gt_answer.strip() in gpt_ans

    results.append(row)
    if i % 10 == 0 or i == len(qa_list):
        print(f"{i}개 완료...")

# 3. 결과 요약
ai_ok = sum(1 for r in results if r['AI-based 정답여부'])
tfidf_ok = sum(1 for r in results if r['TF-IDF 정답여부'])
gpt_ok = sum(1 for r in results if r['GPT 정답여부'])

print("\n=== 자동 테스트 결과 요약 ===")
print(f"AI-based 정답률: {ai_ok}/{len(results)} ({ai_ok/len(results)*100:.1f}%)")
print(f"TF-IDF 정답률: {tfidf_ok}/{len(results)} ({tfidf_ok/len(results)*100:.1f}%)")
print(f"GPT 정답률: {gpt_ok}/{len(results)} ({gpt_ok/len(results)*100:.1f}%)")

# 오답/이상응답 샘플 출력
print("\n--- 오답/이상응답 샘플 (최대 5개) ---")
wrong = [r for r in results if not (r['AI-based 정답여부'] and r['TF-IDF 정답여부'] and r['GPT 정답여부'])]
for r in wrong[:5]:
    print(f"\n질문: {r['질문']}\n정답: {r['정답']}\nAI-based: {r['AI-based 답변']}\nTF-IDF: {r['TF-IDF 답변']}\nGPT: {r['GPT 답변']}") 