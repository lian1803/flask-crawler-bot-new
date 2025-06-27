import pandas as pd
import sqlite3
import os

def create_qa_table():
    """qa_data 테이블 생성"""
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    
    # qa_data 테이블 생성 (추가답변 컬럼 포함)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qa_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            additional_answer TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("qa_data 테이블이 생성되었습니다.")

def check_database_structure():
    """데이터베이스 구조 확인"""
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    
    # 테이블 목록 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("=== 데이터베이스 테이블 목록 ===")
    for table in tables:
        print(f"- {table[0]}")
    
    # qa_data 테이블이 있는지 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='qa_data'")
    if not cursor.fetchone():
        print("\nqa_data 테이블이 없습니다. 생성합니다...")
        conn.close()
        create_qa_table()
        conn = sqlite3.connect('school_data.db')
        cursor = conn.cursor()
    
    # qa_data 테이블 구조 확인
    cursor.execute("PRAGMA table_info(qa_data)")
    columns = cursor.fetchall()
    print("\n=== qa_data 테이블 구조 ===")
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
    
    # 기존 데이터 수 확인
    cursor.execute("SELECT COUNT(*) FROM qa_data")
    count = cursor.fetchone()[0]
    print(f"\n기존 데이터 수: {count}")
    
    conn.close()
    return columns

def add_excel_data():
    """엑셀 데이터를 데이터베이스에 추가"""
    excel_file = '와석초 카카오톡 챗봇 개발을 위한 질문과 답변 의 사본.xlsx'
    
    # 데이터베이스 연결
    conn = sqlite3.connect('school_data.db')
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
                # 추가답변 추출
                additional_answer = row.get('추가답변', '')
                if pd.isna(additional_answer):
                    additional_answer = ''
                
                # 중복 확인
                cursor.execute("SELECT id FROM qa_data WHERE question = ?", (question,))
                existing = cursor.fetchone()
                
                if not existing:
                    # 데이터 삽입 (추가답변 별도 컬럼으로 저장)
                    cursor.execute(
                        "INSERT INTO qa_data (question, answer, additional_answer, category) VALUES (?, ?, ?, ?)",
                        (question, answer, additional_answer, sheet_name)
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

if __name__ == "__main__":
    print("=== 엑셀 데이터를 데이터베이스에 추가하는 스크립트 ===")
    
    # 데이터베이스 구조 확인
    check_database_structure()
    
    # 사용자 확인
    response = input("\n엑셀 데이터를 추가하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        add_excel_data()
    else:
        print("취소되었습니다.") 