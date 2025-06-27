import pandas as pd

# 엑셀 파일 읽기
excel_file = '와석초 카카오톡 챗봇 개발을 위한 질문과 답변 의 사본.xlsx'

# 시트 목록 확인
xl = pd.ExcelFile(excel_file)
print("=== 시트 목록 ===")
print(xl.sheet_names)

# 각 시트별로 데이터 확인
for sheet_name in xl.sheet_names:
    print(f"\n=== {sheet_name} 시트 ===")
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    print(f"행 수: {len(df)}")
    print(f"컬럼: {df.columns.tolist()}")
    print("처음 3행:")
    print(df.head(3))
    print("-" * 50) 