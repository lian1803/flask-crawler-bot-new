import openpyxl
import os
import requests
from PIL import Image
import io
import re

def extract_images_from_excel(excel_file_path, output_folder="images"):
    """엑셀 파일에서 이미지를 추출하여 저장"""
    
    # 출력 폴더 생성
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 워크북 열기
    wb = openpyxl.load_workbook(excel_file_path)
    
    extracted_images = []
    
    for sheet_name in wb.sheetnames:
        print(f"시트 '{sheet_name}' 처리 중...")
        ws = wb[sheet_name]
        
        # 이미지 추출
        for image in ws._images:
            try:
                # 이미지 데이터 가져오기
                img_data = image._data()
                
                # PIL Image로 변환
                img = Image.open(io.BytesIO(img_data))
                
                # 파일명 생성 (시트명_인덱스)
                filename = f"{sheet_name}_{len(extracted_images)}.png"
                filepath = os.path.join(output_folder, filename)
                
                # 이미지 저장
                img.save(filepath)
                print(f"이미지 저장: {filepath}")
                
                extracted_images.append({
                    'filename': filename,
                    'filepath': filepath,
                    'sheet': sheet_name,
                    'size': img.size
                })
                
            except Exception as e:
                print(f"이미지 추출 실패: {e}")
    
    wb.close()
    return extracted_images

def extract_images_from_qa_data():
    """QA 데이터에서 이미지 관련 정보 추출"""
    
    # 이미지 매핑 정보
    image_mapping = {
        "학사일정": {
            "keywords": ["학사일정", "개학", "방학", "졸업", "입학"],
            "filename": "schedule.png"
        },
        "교실 배치도": {
            "keywords": ["교실", "배치", "위치", "반"],
            "filename": "classroom_map.png"
        },
        "정차대": {
            "keywords": ["정차", "등하교", "버스", "통학"],
            "filename": "bus_stop.png"
        },
        "학교시설": {
            "keywords": ["시설", "체육관", "도서관", "보건실"],
            "filename": "facilities.png"
        }
    }
    
    return image_mapping

def create_sample_images():
    """샘플 이미지 생성 (실제 이미지가 없을 경우)"""
    
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    if not os.path.exists("images"):
        os.makedirs("images")
    
    # 샘플 이미지 생성
    sample_images = {
        "schedule.png": {
            "title": "와석초등학교 학사일정",
            "content": "2024년 학사일정\n\n1학기\n- 개학: 3월 4일\n- 방학: 7월 20일\n\n2학기\n- 개학: 8월 26일\n- 방학: 12월 31일"
        },
        "classroom_map.png": {
            "title": "교실 배치도",
            "content": "1층: 1학년 1~3반\n2층: 2학년 1~3반\n3층: 3학년 1~3반\n4층: 4학년 1~3반\n5층: 5학년 1~3반\n6층: 6학년 1~3반"
        },
        "bus_stop.png": {
            "title": "정차대 안내",
            "content": "등교: 오전 8:00~8:30\n하교: 오후 2:00~2:30\n\n정차대 위치:\n- 정문 앞\n- 후문 옆"
        },
        "facilities.png": {
            "title": "학교시설 이용시간",
            "content": "도서관: 9:00~17:00\n체육관: 9:00~18:00\n보건실: 9:00~17:00\n컴퓨터실: 9:00~17:00"
        }
    }
    
    for filename, info in sample_images.items():
        # 이미지 생성 (800x600)
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # 제목 그리기
        try:
            font_large = ImageFont.truetype("arial.ttf", 36)
            font_small = ImageFont.truetype("arial.ttf", 24)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # 제목
        title_bbox = draw.textbbox((0, 0), info["title"], font=font_large)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (800 - title_width) // 2
        draw.text((title_x, 50), info["title"], fill='black', font=font_large)
        
        # 내용
        lines = info["content"].split('\n')
        y = 150
        for line in lines:
            if line.strip():
                draw.text((50, y), line, fill='black', font=font_small)
                y += 40
        
        # 파일 저장
        filepath = os.path.join("images", filename)
        img.save(filepath)
        print(f"샘플 이미지 생성: {filepath}")

def main():
    """메인 함수"""
    print("엑셀 파일에서 이미지 추출 시작...")
    
    # 엑셀 파일들 확인
    excel_files = [
        "와석초_카카오톡_챗봇_개발을_위한_질문과_답변(0702).xlsx",
        "와석초_챗봇_모든질문_변형포함.xlsx"
    ]
    
    extracted_images = []
    
    for excel_file in excel_files:
        if os.path.exists(excel_file):
            print(f"\n{excel_file} 처리 중...")
            try:
                images = extract_images_from_excel(excel_file)
                extracted_images.extend(images)
            except Exception as e:
                print(f"파일 처리 실패: {e}")
    
    if not extracted_images:
        print("\n엑셀에서 이미지를 찾을 수 없습니다. 샘플 이미지를 생성합니다...")
        create_sample_images()
    
    # 이미지 매핑 정보 생성
    image_mapping = extract_images_from_qa_data()
    
    print(f"\n총 {len(extracted_images)}개의 이미지가 추출되었습니다.")
    
    # 결과 출력
    for img in extracted_images:
        print(f"- {img['filename']} ({img['sheet']}) - {img['size']}")

if __name__ == "__main__":
    main() 