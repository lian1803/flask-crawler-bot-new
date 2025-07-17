#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import random
from ai_logic import AILogic
from typing import List, Dict, Tuple

class ComprehensiveTester:
    def __init__(self):
        self.ai = AILogic()
        self.test_results = []
        
        # 테스트 시나리오 정의
        self.scenarios = {
            "개학 관련": [
                "개학 언제야", "개학은 언제하나요?", "개학일", "개학 날짜", "개학 시기",
                "개학이 언제야", "개학이 언제인가요?", "개학일정", "개학 스케줄",
                "개학은 몇월 몇일", "개학 날짜 알려줘", "개학이 언제예요",
                "개학은 언제부터", "개학 시작일", "개학은 언제부터인가요"
            ],
            
            "학교 전화번호 관련": [
                "학교 전화번호", "학교 번호", "학교 연락처", "학교에 전화하고 싶어",
                "학교로 전화하려면", "학교 전화번호 알려줘", "학교 번호 알려줘",
                "학교 연락처 알려줘", "학교에 문의하고 싶어", "학교로 연락하고 싶어",
                "학교 전화번호가 뭐야", "학교 번호가 뭐야", "학교 연락처가 뭐야"
            ],
            
            "급식 관련": [
                "오늘 급식", "오늘 식단", "오늘 점심", "오늘 메뉴", "오늘 밥",
                "내일 급식", "내일 식단", "내일 점심", "내일 메뉴", "내일 밥",
                "어제 급식", "어제 식단", "어제 점심", "어제 메뉴", "어제 밥",
                "모레 급식", "모레 식단", "모레 점심", "모레 메뉴", "모레 밥",
                "급식 메뉴", "식단표", "급식표", "점심 메뉴", "중식 메뉴",
                "5월 20일 급식", "5/20 급식", "5월 20일 식단", "5/20 식단"
            ],
            
            "방과후 관련": [
                "방과후", "방과후 수업", "방과후 프로그램", "방과후 활동",
                "방과후 시간", "방과후 일정", "방과후 스케줄", "방과후 신청",
                "방과후 등록", "방과후 수강", "방과후 교실", "방과후 강사",
                "방과후 비용", "방과후 요금", "방과후 학비", "방과후 수업료"
            ],
            
            "전학 관련": [
                "전학", "전학 절차", "전학 신청", "전학 방법", "전학 과정",
                "전입", "전입 신청", "전입 절차", "전입 방법", "전입 과정",
                "전출", "전출 신청", "전출 절차", "전출 방법", "전출 과정",
                "전학하려면", "전학하고 싶어", "전학 가려고 해", "전학 가려면"
            ],
            
            "상담 관련": [
                "상담", "담임 상담", "선생님 상담", "교사 상담", "상담 신청",
                "상담 예약", "상담 일정", "상담 시간", "상담 방법", "상담 절차",
                "담임과 상담", "선생님과 상담", "교사와 상담", "상담하고 싶어",
                "상담 받고 싶어", "상담 예약하고 싶어", "상담 일정 잡고 싶어"
            ],
            
            "결석 관련": [
                "결석", "결석 신고", "결석 처리", "결석 방법", "결석 절차",
                "결석 사유", "결석 이유", "결석 신고서", "결석 처리 방법",
                "아프면", "병원 갈 것 같아", "몸이 안 좋아", "결석해야 해",
                "결석 신고하고 싶어", "결석 처리하고 싶어", "결석 신고서 제출"
            ],
            
            "교실 배치 관련": [
                "교실", "교실 배치", "교실 위치", "교실 찾기", "교실 번호",
                "3학년 1반", "4학년 2반", "5학년 3반", "6학년 4반",
                "1학년 1반 어디야", "2학년 2반 어디야", "3학년 3반 어디야",
                "교실 배치도", "교실 위치도", "교실 찾는 방법", "교실 번호 알려줘"
            ],
            
            "등하교 관련": [
                "등하교", "등교", "하교", "등교 시간", "하교 시간",
                "등교 방법", "하교 방법", "등교 경로", "하교 경로",
                "등교 버스", "하교 버스", "등교 차량", "하교 차량",
                "등교 정차대", "하교 정차대", "정차대", "정차대 위치",
                "등교 시간이 언제야", "하교 시간이 언제야", "등교 방법 알려줘"
            ],
            
            "학교시설 관련": [
                "학교시설", "체육관", "운동장", "도서관", "도서실",
                "보건실", "급식실", "컴퓨터실", "음악실", "미술실",
                "체육관 사용", "운동장 사용", "도서관 사용", "도서실 사용",
                "학교시설 이용", "학교시설 사용", "체육관 임대", "운동장 임대"
            ],
            
            "유치원 관련": [
                "유치원", "유치원 등원", "유치원 하원", "유치원 시간",
                "유치원 운영시간", "유치원 등원시간", "유치원 하원시간",
                "유치원 방과후", "유치원 특성화", "유치원 프로그램",
                "유치원 등원이 언제야", "유치원 하원이 언제야", "유치원 시간 알려줘"
            ],
            
            "일반적인 질문": [
                "안녕", "안녕하세요", "안녕하세요!", "안녕!", "안녕~",
                "도움", "도움말", "도움말이 필요해", "도움이 필요해",
                "감사", "감사합니다", "고마워", "고마워요", "고맙습니다",
                "뭐해", "뭐하고 있어", "뭐해?", "뭐하고 있어?",
                "잘 있어", "잘 있어요", "잘 있어~", "잘 있어요~"
            ],
            
            "부적절한 내용": [
                "바보", "멍청이", "바보야", "멍청아", "바보같아",
                "싫어", "싫어요", "싫다", "싫어요", "싫어~",
                "화나", "화나요", "화나네", "화나요", "화나~",
                "짜증", "짜증나", "짜증나요", "짜증나네", "짜증나~"
            ],
            
            "와석초와 관련없는 내용": [
                "날씨", "날씨가 어때", "날씨가 어때요", "날씨 알려줘",
                "주식", "주식이 어때", "주식이 어때요", "주식 알려줘",
                "영화", "영화 추천", "영화 추천해줘", "영화 알려줘",
                "음식", "음식 추천", "음식 추천해줘", "음식 알려줘",
                "여행", "여행 추천", "여행 추천해줘", "여행 알려줘"
            ]
        }
        
        # 랜덤 단어 조합 생성
        self.random_combinations = self.generate_random_combinations()
    
    def generate_random_combinations(self) -> List[str]:
        """랜덤 단어 조합 생성"""
        base_words = [
            "개학", "급식", "방과후", "전학", "상담", "결석", "교실", "등하교",
            "학교시설", "유치원", "전화번호", "연락처", "일정", "시간", "방법",
            "절차", "신청", "등록", "예약", "문의", "알려줘", "알려주세요",
            "어디", "언제", "어떻게", "무엇", "왜", "누가", "어떤", "몇"
        ]
        
        modifiers = [
            "하고 싶어", "알고 싶어", "궁금해", "필요해", "찾고 있어",
            "알려줘", "알려주세요", "도와줘", "도와주세요", "부탁해",
            "좋아", "싫어", "어려워", "쉬워", "빨라", "느려", "크고", "작고"
        ]
        
        combinations = []
        
        # 단일 단어
        combinations.extend(base_words)
        
        # 두 단어 조합
        for word1 in base_words[:20]:  # 일부만 사용하여 조합 수 제한
            for word2 in base_words[:20]:
                if word1 != word2:
                    combinations.append(f"{word1} {word2}")
        
        # 단어 + 수식어 조합
        for word in base_words[:30]:
            for modifier in modifiers[:10]:
                combinations.append(f"{word} {modifier}")
        
        # 숫자 조합
        numbers = ["1", "2", "3", "4", "5", "6", "첫째", "둘째", "셋째", "넷째", "다섯째", "여섯째"]
        for number in numbers:
            for word in ["학년", "반", "교실", "시간", "일"]:
                combinations.append(f"{number} {word}")
        
        return combinations[:1000]  # 최대 1000개로 제한
    
    def test_scenario(self, scenario_name: str, questions: List[str]) -> Dict:
        """특정 시나리오 테스트"""
        print(f"\n=== {scenario_name} 테스트 시작 ===")
        results = {
            "scenario": scenario_name,
            "total": len(questions),
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        for i, question in enumerate(questions, 1):
            try:
                start_time = time.time()
                
                # QA 매칭 테스트
                qa_match = self.ai.find_qa_match(question)
                
                # 전체 메시지 처리 테스트
                success, response = self.ai.process_message(question, f"test_user_{i}")
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                result_detail = {
                    "question": question,
                    "qa_match": qa_match is not None,
                    "qa_match_question": qa_match['question'] if qa_match else None,
                    "qa_match_answer": qa_match['answer'] if qa_match else None,
                    "success": success,
                    "response": response,
                    "processing_time": processing_time
                }
                
                results["details"].append(result_detail)
                
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                
                # 진행상황 출력
                if i % 10 == 0:
                    print(f"진행률: {i}/{len(questions)} ({i/len(questions)*100:.1f}%)")
                
                # 너무 빠른 요청 방지
                time.sleep(0.01)
                
            except Exception as e:
                print(f"테스트 중 오류 발생: {question} - {e}")
                results["failed"] += 1
                results["details"].append({
                    "question": question,
                    "error": str(e),
                    "success": False
                })
        
        print(f"=== {scenario_name} 테스트 완료 ===")
        print(f"성공: {results['success']}, 실패: {results['failed']}, 성공률: {results['success']/results['total']*100:.1f}%")
        
        return results
    
    def test_random_combinations(self) -> Dict:
        """랜덤 단어 조합 테스트"""
        print(f"\n=== 랜덤 단어 조합 테스트 시작 (총 {len(self.random_combinations)}개) ===")
        
        results = {
            "scenario": "랜덤 단어 조합",
            "total": len(self.random_combinations),
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        for i, question in enumerate(self.random_combinations, 1):
            try:
                start_time = time.time()
                
                # QA 매칭만 테스트 (전체 처리 대신)
                qa_match = self.ai.find_qa_match(question)
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                result_detail = {
                    "question": question,
                    "qa_match": qa_match is not None,
                    "qa_match_question": qa_match['question'] if qa_match else None,
                    "qa_match_answer": qa_match['answer'] if qa_match else None,
                    "processing_time": processing_time
                }
                
                results["details"].append(result_detail)
                
                if qa_match:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                
                # 진행상황 출력
                if i % 50 == 0:
                    print(f"진행률: {i}/{len(self.random_combinations)} ({i/len(self.random_combinations)*100:.1f}%)")
                
                # 너무 빠른 요청 방지
                time.sleep(0.005)
                
            except Exception as e:
                print(f"테스트 중 오류 발생: {question} - {e}")
                results["failed"] += 1
                results["details"].append({
                    "question": question,
                    "error": str(e)
                })
        
        print(f"=== 랜덤 단어 조합 테스트 완료 ===")
        print(f"매칭 성공: {results['success']}, 매칭 실패: {results['failed']}, 매칭률: {results['success']/results['total']*100:.1f}%")
        
        return results
    
    def run_comprehensive_test(self):
        """종합 테스트 실행"""
        print("🚀 와석초 챗봇 종합 테스트 시작")
        print(f"총 테스트 시나리오: {len(self.scenarios)}개")
        print(f"랜덤 조합: {len(self.random_combinations)}개")
        
        start_time = time.time()
        
        # 시나리오별 테스트
        for scenario_name, questions in self.scenarios.items():
            result = self.test_scenario(scenario_name, questions)
            self.test_results.append(result)
        
        # 랜덤 조합 테스트
        random_result = self.test_random_combinations()
        self.test_results.append(random_result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 결과 요약
        self.print_summary(total_time)
        
        # 상세 결과 저장
        self.save_detailed_results()
    
    def print_summary(self, total_time: float):
        """테스트 결과 요약 출력"""
        print("\n" + "="*60)
        print("📊 종합 테스트 결과 요약")
        print("="*60)
        
        total_questions = 0
        total_success = 0
        total_failed = 0
        
        for result in self.test_results:
            total_questions += result["total"]
            total_success += result["success"]
            total_failed += result["failed"]
            
            print(f"\n📋 {result['scenario']}:")
            print(f"   총 질문: {result['total']}")
            print(f"   성공: {result['success']}")
            print(f"   실패: {result['failed']}")
            if result["total"] > 0:
                success_rate = result["success"] / result["total"] * 100
                print(f"   성공률: {success_rate:.1f}%")
        
        print(f"\n🎯 전체 결과:")
        print(f"   총 질문 수: {total_questions}")
        print(f"   총 성공: {total_success}")
        print(f"   총 실패: {total_failed}")
        if total_questions > 0:
            overall_success_rate = total_success / total_questions * 100
            print(f"   전체 성공률: {overall_success_rate:.1f}%")
        
        print(f"   총 소요 시간: {total_time:.2f}초")
        print(f"   평균 처리 시간: {total_time/total_questions*1000:.2f}ms/질문")
        
        # 성능 분석
        self.analyze_performance()
    
    def analyze_performance(self):
        """성능 분석"""
        print(f"\n🔍 성능 분석:")
        
        # 처리 시간 분석
        all_processing_times = []
        for result in self.test_results:
            for detail in result["details"]:
                if "processing_time" in detail:
                    all_processing_times.append(detail["processing_time"])
        
        if all_processing_times:
            avg_time = sum(all_processing_times) / len(all_processing_times)
            max_time = max(all_processing_times)
            min_time = min(all_processing_times)
            
            print(f"   평균 처리 시간: {avg_time*1000:.2f}ms")
            print(f"   최대 처리 시간: {max_time*1000:.2f}ms")
            print(f"   최소 처리 시간: {min_time*1000:.2f}ms")
        
        # 시나리오별 성공률 분석
        print(f"\n📈 시나리오별 성공률:")
        for result in self.test_results:
            if result["total"] > 0:
                success_rate = result["success"] / result["total"] * 100
                print(f"   {result['scenario']}: {success_rate:.1f}%")
    
    def save_detailed_results(self):
        """상세 결과를 파일로 저장"""
        import json
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 상세 결과가 {filename}에 저장되었습니다.")

if __name__ == "__main__":
    tester = ComprehensiveTester()
    tester.run_comprehensive_test() 