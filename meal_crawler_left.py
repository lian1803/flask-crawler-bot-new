from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import json
import time
import re

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)

def extract_weekday_lunch(driver):
    # 월~금 중식 tr[2], td[2]~td[6], 각 td의 p[4] 텍스트만 추출
    results = []
    date_els = driver.find_elements(By.CSS_SELECTOR, 'thead tr th')[1:]
    dates = [el.text.split('\n')[1] for el in date_els]
    for i in range(1, 6):
        menu = ''
        img_url = ''
        try:
            xpath = f'//*[@id="detailForm"]/div/table/tbody/tr[2]/td[{i+1}]/p[4]'
            menu = driver.find_element(By.XPATH, xpath).text.strip()
        except StaleElementReferenceException:
            print(f'[WARN] StaleElementReferenceException: menu {i}')
            continue
        except Exception:
            pass
        try:
            td_xpath = f'//*[@id="detailForm"]/div/table/tbody/tr[2]/td[{i+1}]'
            td_html = driver.find_element(By.XPATH, td_xpath).get_attribute('innerHTML')
            img_match = re.search(r'<img[^>]+src=["\"]([^"\"]+)["\"]', td_html)
            if img_match:
                img_url = img_match.group(1)
        except StaleElementReferenceException:
            print(f'[WARN] StaleElementReferenceException: img {i}')
            continue
        except Exception:
            pass
        results.append({
            'date': dates[i],
            'meal_type': '중식',
            'menu': menu,
            'image_url': img_url
        })
    return results

def main():
    driver = setup_driver()
    results = []
    try:
        print('[INFO] 페이지 진입 시도')
        driver.get('https://pajuwaseok-e.goepj.kr/pajuwaseok-e/ad/fm/foodmenu/selectFoodMenuView.do?mi=8432')
        week_count = 0
        while True:
            try:
                print(f'[INFO] {week_count+1}번째 주 월~금 중식 데이터 수집 시작')
                week_data = extract_weekday_lunch(driver)
                print(f'[DEBUG] {week_count+1}번째 주 데이터 개수: {len(week_data)}')
                if not any(item['menu'] for item in week_data):
                    print('[INFO] 더 이상 데이터 없음, 종료')
                    break
                results.extend(week_data)
                try:
                    date_els = driver.find_elements(By.CSS_SELECTOR, 'thead tr th')[1:]
                    prev_dates = [el.text.split('\n')[1] for el in date_els]
                    prev_btn = driver.find_element(By.CSS_SELECTOR, 'a:has(i.xi-angle-right)')
                    print('[INFO] 다음주 버튼 클릭')
                    prev_btn.click()
                    WebDriverWait(driver, 10).until(
                        lambda d: [el.text.split('\n')[1] for el in d.find_elements(By.CSS_SELECTOR, 'thead tr th')[1:]] != prev_dates
                    )
                    time.sleep(0.5)
                    week_count += 1
                    continue
                except NoSuchElementException:
                    print('[WARN] 더 이상 이전주 버튼 없음')
                    break
            except StaleElementReferenceException:
                print('[WARN] StaleElementReferenceException: 루프에서 발생, 다음 주로 진행')
                continue
    except Exception as e:
        print(f"[ERROR] 크롤링 중 오류 발생: {str(e)}")
    finally:
        try:
            with open('meals_result.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n[INFO] 총 {len(results)}개의 식단 데이터가 저장되었습니다.")
        except Exception as e:
            print(f"[ERROR] 결과 저장 중 오류 발생: {str(e)}")
        finally:
            driver.quit()

if __name__ == "__main__":
    main() 