import openpyxl
wb = openpyxl.load_workbook('와석초 카카오톡 챗봇 개발을 위한 질문과 답변(0702).xlsx')
with open('sheets.txt', 'w', encoding='utf-8') as f:
    for name in wb.sheetnames:
        f.write(name + '\n')
wb.close() 