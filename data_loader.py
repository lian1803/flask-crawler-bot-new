import sqlite3
import json
import os

def load_meals_to_db():
    """식단 데이터를 데이터베이스에 로드"""
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    
    # 기존 데이터 삭제
    cursor.execute('DELETE FROM meals')
    
    # meal_crawler_left.json 로드
    if os.path.exists('meal_crawler_left.json'):
        with open('meal_crawler_left.json', 'r', encoding='utf-8') as f:
            meals_data = json.load(f)
            
        for meal in meals_data:
            cursor.execute('''
                INSERT INTO meals (date, meal_type, menu, image_url)
                VALUES (?, ?, ?, ?)
            ''', (meal['date'], meal['meal_type'], meal['menu'], meal['image_url']))
        
        print(f"식단 데이터 {len(meals_data)}개 로드 완료")
    
    # meals_result_right.json 로드 (중복 제거)
    if os.path.exists('meals_result_right.json'):
        with open('meals_result_right.json', 'r', encoding='utf-8') as f:
            meals_data = json.load(f)
            
        for meal in meals_data:
            # 중복 체크
            cursor.execute('SELECT id FROM meals WHERE date = ? AND meal_type = ?', 
                         (meal['date'], meal['meal_type']))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO meals (date, meal_type, menu, image_url)
                    VALUES (?, ?, ?, ?)
                ''', (meal['date'], meal['meal_type'], meal['menu'], meal['image_url']))
        
        print(f"추가 식단 데이터 로드 완료")
    
    conn.commit()
    conn.close()

def load_notices_to_db():
    """공지사항 데이터를 데이터베이스에 로드"""
    conn = sqlite3.connect('school_data.db')
    cursor = conn.cursor()
    
    # 기존 데이터 삭제
    cursor.execute('DELETE FROM notices')
    
    # notice_result.json이 있다면 로드
    if os.path.exists('notice_result.json'):
        with open('notice_result.json', 'r', encoding='utf-8') as f:
            notices_data = json.load(f)
            
        for notice in notices_data:
            cursor.execute('''
                INSERT INTO notices (title, content, url, created_at, tags, category)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (notice['title'], notice['content'], notice['url'], 
                 notice['created_at'], notice['tags'], notice['category']))
        
        print(f"공지사항 데이터 {len(notices_data)}개 로드 완료")
    else:
        print("공지사항 데이터 파일이 없습니다.")

def main():
    print("데이터베이스 로딩 시작...")
    load_meals_to_db()
    load_notices_to_db()
    print("데이터베이스 로딩 완료!")

if __name__ == "__main__":
    main() 