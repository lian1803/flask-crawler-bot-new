import sqlite3

def test_qa_logic():
    """개선된 QA 로직 테스트"""
    
    # 1. qa_data 확인
    print("=== qa_data 테이블 확인 ===")
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT question, answer, additional_answer FROM qa_data WHERE question LIKE "%끝나%" LIMIT 3')
    qa_results = cursor.fetchall()
    
    for q, a, add in qa_results:
        print(f"Q: {q}")
        print(f"A: {a}")
        print(f"추가: {add}")
        print("---")
    
    # 2. notices 테이블에서 시정표 관련 확인
    print("\n=== notices 테이블에서 시정표 관련 확인 ===")
    cursor.execute('SELECT title, content FROM notices WHERE title LIKE "%시정표%" OR content LIKE "%시정표%" LIMIT 3')
    notice_results = cursor.fetchall()
    
    for title, content in notice_results:
        print(f"제목: {title}")
        if content:
            print(f"내용: {content[:100]}...")
        print("---")
    
    conn.close()

if __name__ == "__main__":
    test_qa_logic() 