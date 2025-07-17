#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd

def check_excel_file():
    filename = '와석초_챗봇_모든질문_변형포함.xlsx'
    
    print(f"📊 엑셀 파일 분석: {filename}")
    print("=" * 50)
    
    # 엑셀 파일의 모든 시트 확인
    excel_file = pd.ExcelFile(filename)
    print(f"📋 시트 목록: {excel_file.sheet_names}")
    print()
    
    # 전체질문 시트 확인
    print("📈 전체질문 시트 분석:")
    df_all = pd.read_excel(filename, sheet_name='전체질문')
    print(f"  - 총 행 수: {len(df_all)}")
    print(f"  - 총 열 수: {len(df_all.columns)}")
    print(f"  - 열 이름: {list(df_all.columns)}")
    print()
    
    # 원본질문만 시트 확인
    print("📈 원본질문만 시트 분석:")
    df_original = pd.read_excel(filename, sheet_name='원본질문만')
    print(f"  - 총 행 수: {len(df_original)}")
    print()
    
    # 통계 시트 확인
    print("📈 통계 시트 분석:")
    df_stats = pd.read_excel(filename, sheet_name='통계')
    print(f"  - 총 행 수: {len(df_stats)}")
    print("  - 카테고리별 통계:")
    for _, row in df_stats.iterrows():
        print(f"    {row['카테고리']}: 원본 {row['원본 질문 수']}개, 변형 {row['변형 질문 수']}개, 총 {row['총 질문 수']}개")
    print()
    
    # 샘플 데이터 확인
    print("🔍 샘플 데이터 (처음 10개):")
    print(df_all.head(10)[['원본 질문', '질문', '카테고리', '변형 타입']].to_string(index=False))
    print()
    
    # 카테고리별 분포 확인
    print("📊 카테고리별 분포:")
    category_counts = df_all['카테고리'].value_counts()
    for category, count in category_counts.items():
        print(f"  - {category}: {count}개")
    print()
    
    # 변형 타입별 분포 확인
    print("📊 변형 타입별 분포:")
    type_counts = df_all['변형 타입'].value_counts()
    for type_name, count in type_counts.items():
        print(f"  - {type_name}: {count}개")
    print()
    
    # 오타 변형 예시 확인
    print("🔍 오타 변형 예시:")
    sample_questions = df_all[df_all['변형 타입'] == '변형'].head(5)
    for _, row in sample_questions.iterrows():
        print(f"  원본: {row['원본 질문']}")
        print(f"  변형: {row['질문']}")
        print(f"  카테고리: {row['카테고리']}")
        print()

if __name__ == "__main__":
    check_excel_file() 