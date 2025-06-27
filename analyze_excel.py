import pandas as pd

# 엑셀 파일 읽기
excel_file = '와석초 카카오톡 챗봇 개발을 위한 질문과 답변 의 사본.xlsx'

# 각 시트별로 데이터 분석
for sheet_name in ['초등', '유치원']:
    print(f"\n{'='*60}")
    print(f"=== {sheet_name} 시트 분석 ===")
    print(f"{'='*60}")
    
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    print(f"총 행 수: {len(df)}")
    print(f"컬럼: {df.columns.tolist()}")
    
    # 질문과 답변 추출
    questions = df['질문 예시'].dropna()
    answers = df['답변 '].dropna()
    
    print(f"\n질문 수: {len(questions)}")
    print(f"답변 수: {len(answers)}")
    
    print(f"\n=== {sheet_name} 질문 예시 (처음 10개) ===")
    for i, q in enumerate(questions.head(10)):
        print(f"{i+1}. {q}")
    
    print(f"\n=== {sheet_name} 답변 예시 (처음 10개) ===")
    for i, a in enumerate(answers.head(10)):
        print(f"{i+1}. {a}")
    
    # 추가답변 컬럼이 있는지 확인
    if '추가답변' in df.columns:
        additional_answers = df['추가답변'].dropna()
        if len(additional_answers) > 0:
            print(f"\n=== {sheet_name} 추가답변 (처음 5개) ===")
            for i, a in enumerate(additional_answers.head(5)):
                print(f"{i+1}. {a}")
    
    print("\n" + "-"*60) 