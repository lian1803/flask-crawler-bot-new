import pandas as pd
import sqlite3
import os

def create_qa_table():
    """qa_data 테이블 생성"""
    conn = sqlite3.connect('../school_data.db')
    cursor = conn.cursor()
    
    # qa_data 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qa_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("qa_data 테이블이 생성되었습니다.")
    conn.commit()
    conn.close()

def add_excel_data():
    """엑셀 데이터를 데이터베이스에 추가"""
    excel_file = '와석초 카카오톡 챗봇 개발을 위한 질문과 답변 의 사본.xlsx'
    
    # 데이터베이스 연결
    conn = sqlite3.connect('../school_data.db')
    cursor = conn.cursor()
    
    total_added = 0
    
    # 각 시트별로 데이터 추가
    for sheet_name in ['초등', '유치원']:
        print(f"\n=== {sheet_name} 시트 처리 중 ===")
        
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
        # 질문과 답변 추출
        for index, row in df.iterrows():
            question = row['질문 예시']
            answer = row['답변 ']
            
            # 빈 값이 아닌 경우만 처리
            if pd.notna(question) and pd.notna(answer):
                # 추가답변이 있는 경우 합치기
                additional_answer = row.get('추가답변', '')
                if pd.notna(additional_answer):
                    full_answer = f"{answer}\n\n추가 정보: {additional_answer}"
                else:
                    full_answer = answer
                
                # 중복 확인
                cursor.execute("SELECT id FROM qa_data WHERE question = ?", (question,))
                existing = cursor.fetchone()
                
                if not existing:
                    # 데이터 삽입
                    cursor.execute(
                        "INSERT INTO qa_data (question, answer, category) VALUES (?, ?, ?)",
                        (question, full_answer, sheet_name)
                    )
                    total_added += 1
                    print(f"추가됨: {question[:30]}...")
                else:
                    print(f"중복됨: {question[:30]}...")
    
    # 변경사항 저장
    conn.commit()
    conn.close()
    
    print(f"\n=== 완료 ===")
    print(f"총 {total_added}개의 새로운 질문/답변 쌍이 추가되었습니다.")

def check_results():
    """결과 확인"""
    conn = sqlite3.connect('../school_data.db')
    cursor = conn.cursor()
    
    # 전체 데이터 수 확인
    cursor.execute("SELECT COUNT(*) FROM qa_data")
    total_count = cursor.fetchone()[0]
    print(f"\n총 qa_data 수: {total_count}")
    
    # 카테고리별 데이터 수 확인
    cursor.execute("SELECT category, COUNT(*) FROM qa_data GROUP BY category")
    category_counts = cursor.fetchall()
    print("\n카테고리별 데이터 수:")
    for category, count in category_counts:
        print(f"- {category}: {count}개")
    
    # 샘플 데이터 확인
    cursor.execute("SELECT question, answer, category FROM qa_data LIMIT 3")
    samples = cursor.fetchall()
    print("\n샘플 데이터:")
    for i, (question, answer, category) in enumerate(samples, 1):
        print(f"{i}. [{category}] {question[:50]}...")
    
    conn.close()

if __name__ == "__main__":
    print("=== qa_data 테이블 생성 및 엑셀 데이터 추가 ===")
    
    # 테이블 생성
    create_qa_table()
    
    # 엑셀 데이터 추가
    add_excel_data()
    
    # 결과 확인
    check_results() 