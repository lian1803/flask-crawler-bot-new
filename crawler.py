import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import os

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service()
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(3)
    return driver

def extract_notice_content(driver):
    try:
        el = driver.find_element(By.CSS_SELECTOR, "div.bbsV_cont")
        return el.text.strip()
    except Exception:
        return ""

def save_notices(notices, filename="notice_result.json"):
    # 기존 데이터가 있으면 로드
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            # 중복 제거를 위해 제목 기준으로 딕셔너리 생성
            notices_dict = {notice["title"]: notice for notice in existing_data}
            # 새로운 데이터 추가
            for notice in notices:
                notices_dict[notice["title"]] = notice
            # 다시 리스트로 변환
            notices = list(notices_dict.values())
    
    # ID 재정렬
    for i, notice in enumerate(notices, 1):
        notice["id"] = i
    
    # 저장
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(notices, f, ensure_ascii=False, indent=2)

def crawl_top_notices(driver, total_count=500, per_page=10):
    url = "https://pajuwaseok-e.goepj.kr/pajuwaseok-e/na/ntt/selectNttList.do?mi=8476&bbsId=5794"
    notices = []
    seen_titles = set()
    page = 1
    
    # 기존 데이터 로드
    if os.path.exists("notice_result.json"):
        with open("notice_result.json", "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            seen_titles = {notice["title"] for notice in existing_data}
            notices = existing_data
    
    while len(notices) < total_count:
        print(f"\n=== 페이지 {page} 시작 ===")
        if page == 1:
            driver.get(url)
        else:
            print("페이지네이션 버튼 클릭 시도...")
            btn = driver.find_element(By.CSS_SELECTOR, f"a[onclick*='goPaging({page})']")
            btn.click()
            time.sleep(2)
            print("페이지네이션 버튼 클릭 완료")
        
        # 현재 페이지의 모든 링크 가져오기
        links = driver.find_elements(By.CSS_SELECTOR, "table tbody tr td.ta_l > a")
        print(f"현재 페이지 링크 수: {len(links)}")
        
        for i in range(len(links)):
            if len(notices) >= total_count:
                break
                
            try:
                # 매 반복마다 links 재조회
                links = driver.find_elements(By.CSS_SELECTOR, "table tbody tr td.ta_l > a")
                a = links[i]
                title = a.text.strip()
                print(f"\n처리 중인 글: {title}")
                
                if title in seen_titles:
                    print("이미 처리한 글, 건너뜀")
                    continue
                    
                seen_titles.add(title)
                row = a.find_element(By.XPATH, "./ancestor::tr")
                
                try:
                    created_at = row.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text.strip()
                except Exception:
                    created_at = ""
                
                print("상세 페이지로 이동 시도...")
                a.click()
                time.sleep(1)
                
                detail_url = driver.current_url
                content = extract_notice_content(driver)
                print(f"본문 길이: {len(content)}")
                
                driver.back()
                time.sleep(1)
                print("목록으로 복귀 완료")
                
                new_notice = {
                    "id": len(notices) + 1,
                    "title": title,
                    "url": detail_url,
                    "content": content,
                    "created_at": created_at,
                    "tags": title,
                    "category": None
                }
                
                notices.append(new_notice)
                # 글 하나 크롤링할 때마다 저장
                save_notices(notices)
                print(f"현재까지 크롤링된 글 수: {len(notices)}")
                
            except StaleElementReferenceException:
                print(f"요소 참조 오류 발생, 다음 항목으로 진행")
                continue
            except Exception as e:
                print(f"크롤링 중 오류 발생: {str(e)}")
                continue
                
        page += 1
        
    return notices

def main():
    driver = setup_driver()
    try:
        notices = crawl_top_notices(driver, total_count=500, per_page=10)
        save_notices(notices)  # 최종 저장
    finally:
        driver.quit()

if __name__ == "__main__":
    main() 