import sqlite3

conn = sqlite3.connect('school_data.db')
cursor = conn.cursor()

print("=== qa_data 테이블 샘플 ===")
cursor.execute('SELECT question, answer, additional_answer FROM qa_data LIMIT 5')
results = cursor.fetchall()

for q, a, add in results:
    print(f"Q: {q}")
    print(f"A: {a}")
    print(f"추가: {add}")
    print("---")

conn.close() 