from database import DatabaseManager

db = DatabaseManager()
data = db.get_qa_data()

print(f'총 데이터 수: {len(data)}')
print('\n처음 15개 샘플:')
for i, d in enumerate(data[:15]):
    print(f'[{i+1}] 질문: {d["question"]}')
    print(f'    답변: {d["answer"]}')
    print(f'    카테고리: {d["category"]}')
    print('---')

print('\n카테고리별 데이터 수:')
categories = {}
for d in data:
    cat = d['category']
    categories[cat] = categories.get(cat, 0) + 1

for cat, count in categories.items():
    print(f'{cat}: {count}개') 