#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
자동 크롤링 시스템 테스트 스크립트
"""

import requests
import json
import time
from datetime import datetime

def test_crawler_endpoints():
    """크롤링 관련 엔드포인트 테스트"""
    
    base_url = "http://localhost:5000"  # 로컬 테스트용
    
    print("🧪 자동 크롤링 시스템 테스트 시작")
    print("=" * 50)
    
    # 1. 스케줄러 상태 확인
    print("1️⃣ 스케줄러 상태 확인")
    try:
        response = requests.get(f"{base_url}/scheduler/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 스케줄러 실행 중: {data['scheduler_running']}")
            print(f"📋 등록된 작업: {len(data['jobs'])}개")
            for job in data['jobs']:
                print(f"   - {job['name']}: {job['next_run']}")
        else:
            print(f"❌ 스케줄러 상태 확인 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 스케줄러 상태 확인 오류: {e}")
    
    print()
    
    # 2. 수동 크롤링 실행
    print("2️⃣ 수동 크롤링 실행")
    try:
        response = requests.post(f"{base_url}/crawl")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 크롤링 성공: {data['message']}")
        else:
            print(f"❌ 크롤링 실패: {response.status_code}")
            print(f"응답: {response.text}")
    except Exception as e:
        print(f"❌ 크롤링 실행 오류: {e}")
    
    print()
    
    # 3. 통계 정보 확인
    print("3️⃣ 통계 정보 확인")
    try:
        response = requests.get(f"{base_url}/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ QA 데이터: {data['qa_data_count']}개")
            print(f"✅ 최근 대화: {data['recent_conversations']}개")
            print(f"✅ 서버 상태: {data['server_status']}")
        else:
            print(f"❌ 통계 확인 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 통계 확인 오류: {e}")
    
    print()
    
    # 4. 헬스 체크
    print("4️⃣ 헬스 체크")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 서버 상태: {data['status']}")
            print(f"✅ 데이터베이스: {data['database']}")
        else:
            print(f"❌ 헬스 체크 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 헬스 체크 오류: {e}")
    
    print()
    print("🎉 테스트 완료!")

def test_crawler_direct():
    """크롤러 직접 실행 테스트"""
    print("🔄 크롤러 직접 실행 테스트")
    print("=" * 30)
    
    try:
        import subprocess
        result = subprocess.run(['python', 'incremental_notice_crawler.py'], 
                              capture_output=True, text=True, timeout=60)
        
        print("📤 크롤러 출력:")
        print(result.stdout)
        
        if result.stderr:
            print("❌ 크롤러 오류:")
            print(result.stderr)
        
        print(f"✅ 크롤러 실행 완료 (종료 코드: {result.returncode})")
        
    except subprocess.TimeoutExpired:
        print("⏰ 크롤러 실행 시간 초과 (60초)")
    except Exception as e:
        print(f"❌ 크롤러 실행 오류: {e}")

if __name__ == "__main__":
    print("🚀 자동 크롤링 시스템 테스트")
    print(f"⏰ 테스트 시작 시간: {datetime.now()}")
    print()
    
    # 1. 크롤러 직접 실행 테스트
    test_crawler_direct()
    print()
    
    # 2. 웹 엔드포인트 테스트 (서버가 실행 중일 때만)
    try:
        test_crawler_endpoints()
    except requests.exceptions.ConnectionError:
        print("⚠️  서버가 실행되지 않아 엔드포인트 테스트를 건너뜁니다.")
        print("   서버를 먼저 실행한 후 다시 테스트해주세요.")
    
    print()
    print("🏁 모든 테스트 완료!") 