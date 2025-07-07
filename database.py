import sqlite3
import pandas as pd
import os
from datetime import datetime
from config import db_path, excel_file

class SchoolDatabase:
    def __init__(self):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 공지사항 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                url TEXT,
                created_at TEXT,
                tags TEXT,
                category TEXT
            )
        ''')
        
        # 식단 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                meal_type TEXT,
                menu TEXT,
                image_url TEXT
            )
        ''')
        
        # QA 데이터 테이블
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
    
    def get_meal_info(self, date=None):
        """특정 날짜의 식단 정보를 가져옵니다."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        weekday = datetime.strptime(date, "%Y-%m-%d").weekday()
        if weekday >= 5:  # 주말
            return {"date": date, "menu": f"{date}는 주말(토/일)이라 급식이 없습니다."}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT menu FROM meals WHERE date = ? AND meal_type = "중식"', (date,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return {"date": date, "menu": result[0]}
        else:
            return {"date": date, "menu": f"{date}에는 식단 정보가 없습니다."}
    
    def get_latest_notices(self, limit=5):
        """최신 공지사항을 가져옵니다."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT title, content, created_at, category 
            FROM notices 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        results = cursor.fetchall()
        conn.close()
        
        notices = []
        for row in results:
            notices.append({
                "title": row[0],
                "content": row[1],
                "created_at": row[2],
                "category": row[3]
            })
        return notices
    
    def search_qa_data(self, question, category=None):
        """QA 데이터에서 질문에 맞는 답변을 검색합니다."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT answer, additional_answer, category 
                FROM qa_data 
                WHERE question = ? AND category = ?
            ''', (question, category))
        else:
            cursor.execute('''
                SELECT answer, additional_answer, category 
                FROM qa_data 
                WHERE question = ?
            ''', (question,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "answer": result[0],
                "additional_answer": result[1],
                "category": result[2]
            }
        return None
    
    def search_qa_by_keyword(self, keyword, limit=5):
        """키워드로 QA 데이터를 검색합니다."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT question, answer, category 
            FROM qa_data 
            WHERE question LIKE ? OR answer LIKE ?
            LIMIT ?
        ''', (f'%{keyword}%', f'%{keyword}%', limit))
        results = cursor.fetchall()
        conn.close()
        
        qa_list = []
        for row in results:
            qa_list.append({
                "question": row[0],
                "answer": row[1],
                "category": row[2]
            })
        return qa_list
    
    def get_all_qa_data(self):
        """모든 QA 데이터를 가져옵니다 (AI 컨텍스트용)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT question, answer, category FROM qa_data')
        results = cursor.fetchall()
        conn.close()
        
        qa_data = []
        for row in results:
            qa_data.append({
                "question": row[0],
                "answer": row[1],
                "category": row[2]
            })
        return qa_data
    
    def update_excel_data(self):
        """엑셀 파일에서 데이터를 업데이트합니다."""
        if not os.path.exists(excel_file):
            print(f"엑셀 파일을 찾을 수 없습니다: {excel_file}")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            total_added = 0
            xl = pd.ExcelFile(excel_file)
            
            for sheet_name in xl.sheet_names:
                print(f"{sheet_name} 시트 처리 중...")
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                if sheet_name in ['초등', '유치원']:
                    for index, row in df.iterrows():
                        question = row.get('질문 예시', None)
                        answer = row.get('답변 ', None)
                        additional_answer = row.get('추가답변', '')
                        
                        if pd.isna(additional_answer):
                            additional_answer = ''
                        
                        if pd.notna(question) and pd.notna(answer):
                            cursor.execute(
                                "SELECT id FROM qa_data WHERE question = ? AND category = ?", 
                                (question, sheet_name)
                            )
                            existing = cursor.fetchone()
                            
                            if not existing:
                                cursor.execute(
                                    "INSERT INTO qa_data (question, answer, additional_answer, category) VALUES (?, ?, ?, ?)",
                                    (question, answer, additional_answer, sheet_name)
                                )
                                total_added += 1
                else:
                    # 기타 시트 처리
                    for index, row in df.iterrows():
                        columns = df.columns.tolist()
                        question = row.get(columns[0], None)
                        answer = row.get(columns[1], None) if len(columns) > 1 else ''
                        additional_answer = ''
                        
                        if len(columns) > 2:
                            additional_parts = [str(row.get(col, '')) for col in columns[2:] if pd.notna(row.get(col, ''))]
                            additional_answer = '\n'.join(additional_parts)
                        
                        if pd.notna(question) and pd.notna(answer):
                            cursor.execute(
                                "SELECT id FROM qa_data WHERE question = ? AND category = ?", 
                                (str(question), sheet_name)
                            )
                            existing = cursor.fetchone()
                            
                            if not existing:
                                cursor.execute(
                                    "INSERT INTO qa_data (question, answer, additional_answer, category) VALUES (?, ?, ?, ?)",
                                    (str(question), str(answer), additional_answer, sheet_name)
                                )
                                total_added += 1
            
            conn.commit()
            conn.close()
            
            print(f"엑셀 데이터 업데이트 완료 - 총 {total_added}개 추가됨")
            return True
            
        except Exception as e:
            print(f"엑셀 데이터 업데이트 중 오류: {str(e)}")
            return False
    
    def get_db_status(self):
        """데이터베이스 상태를 확인합니다."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # QA 데이터 개수
        cursor.execute('SELECT COUNT(*) FROM qa_data')
        qa_count = cursor.fetchone()[0]
        
        # 급식 데이터 개수
        cursor.execute('SELECT COUNT(*) FROM meals')
        meal_count = cursor.fetchone()[0]
        
        # 공지사항 개수
        cursor.execute('SELECT COUNT(*) FROM notices')
        notice_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "qa_data_count": qa_count,
            "meal_data_count": meal_count,
            "notice_count": notice_count,
            "last_updated": datetime.now().isoformat()
        } 