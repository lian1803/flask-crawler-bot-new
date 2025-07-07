import sqlite3
from datetime import datetime

def check_old_database():
    """기존 DB 파일의 구조와 6월 이후 급식 데이터 확인"""
    try:
        conn = sqlite3.connect('새 폴더/school_data.db')
        cursor = conn.cursor()
        
        # 1. 테이블 목록 확인
        print("=== 기존 DB 테이블 목록 ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"- {table[0]}")
        
        print("\n" + "="*50)
        
        # 2. meals 테이블이 있는지 확인하고 6월 이후 데이터 조회
        if ('meals',) in tables:
            print("=== meals 테이블 구조 ===")
            cursor.execute("PRAGMA table_info(meals)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"- {col[1]} ({col[2]})")
            
            print("\n=== 6월 이후 급식 데이터 ===")
            cursor.execute("""
                SELECT date, meal_type, menu 
                FROM meals 
                WHERE date >= '2024-06-01' 
                ORDER BY date DESC 
                LIMIT 10
            """)
            meals = cursor.fetchall()
            
            if meals:
                print(f"6월 이후 급식 데이터: {len(meals)}개")
                for meal in meals:
                    print(f"- {meal[0]} ({meal[1]}): {meal[2][:50]}...")
            else:
                print("6월 이후 급식 데이터가 없습니다.")
                
            # 전체 급식 데이터 개수
            cursor.execute("SELECT COUNT(*) FROM meals")
            total_meals = cursor.fetchone()[0]
            print(f"\n전체 급식 데이터 개수: {total_meals}개")
            
            # 가장 최근 급식 데이터
            cursor.execute("SELECT date, meal_type, menu FROM meals ORDER BY date DESC LIMIT 1")
            latest_meal = cursor.fetchone()
            if latest_meal:
                print(f"가장 최근 급식: {latest_meal[0]} ({latest_meal[1]})")
        
        # 3. 다른 테이블들도 확인
        for table in tables:
            if table[0] != 'meals':
                print(f"\n=== {table[0]} 테이블 데이터 개수 ===")
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"{table[0]}: {count}개")
                
                # 샘플 데이터 3개
                cursor.execute(f"SELECT * FROM {table[0]} LIMIT 3")
                samples = cursor.fetchall()
                if samples:
                    print("샘플 데이터:")
                    for i, sample in enumerate(samples, 1):
                        print(f"  {i}. {sample}")
        
        conn.close()
        
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    check_old_database() 