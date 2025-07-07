import sqlite3
from datetime import datetime

def check_latest_data():
    """현재 DB에서 각 테이블의 최신 데이터 날짜 확인"""
    try:
        conn = sqlite3.connect('새 폴더/school_data.db')
        cursor = conn.cursor()
        
        print("=== 현재 DB 최신 데이터 확인 ===")
        
        # 1. meals 테이블 최신 날짜
        cursor.execute("SELECT MAX(date) FROM meals")
        latest_meal_date = cursor.fetchone()[0]
        print(f"급식 최신 날짜: {latest_meal_date}")
        
        # 2. notices 테이블 최신 날짜
        cursor.execute("SELECT MAX(created_at) FROM notices")
        latest_notice_date = cursor.fetchone()[0]
        print(f"공지사항 최신 날짜: {latest_notice_date}")
        
        # 3. qa_data 테이블 최신 날짜
        cursor.execute("SELECT MAX(created_at) FROM qa_data")
        latest_qa_date = cursor.fetchone()[0]
        print(f"QA 데이터 최신 날짜: {latest_qa_date}")
        
        # 4. 각 테이블 데이터 개수
        cursor.execute("SELECT COUNT(*) FROM meals")
        meal_count = cursor.fetchone()[0]
        print(f"급식 데이터 개수: {meal_count}")
        
        cursor.execute("SELECT COUNT(*) FROM notices")
        notice_count = cursor.fetchone()[0]
        print(f"공지사항 개수: {notice_count}")
        
        cursor.execute("SELECT COUNT(*) FROM qa_data")
        qa_count = cursor.fetchone()[0]
        print(f"QA 데이터 개수: {qa_count}")
        
        conn.close()
        
        return {
            'latest_meal_date': latest_meal_date,
            'latest_notice_date': latest_notice_date,
            'latest_qa_date': latest_qa_date,
            'meal_count': meal_count,
            'notice_count': notice_count,
            'qa_count': qa_count
        }
        
    except Exception as e:
        print(f"오류 발생: {e}")
        return None

if __name__ == "__main__":
    check_latest_data() 