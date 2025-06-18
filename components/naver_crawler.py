import os
import re
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from components.get_store_and_address import extract_store_and_address
from components.add_travel import add_travel
from components.deepl import translate_text


from typing import Tuple, List, Dict, Any
import os
import re
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from components.get_store_and_address import extract_store_and_address
from components.add_travel import add_travel
from components.deepl import translate_text


def get_chrome_driver() -> webdriver.Chrome:
    """크롬 드라이버 객체 생성"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=chrome_options)


def extract_blog_title(driver: webdriver.Chrome) -> Tuple[str, str]:
    """블로그 제목 추출 및 영문 번역"""
    title = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "se-title-text"))
    ).text.strip()
    safe_title = re.sub(r'[\\/*?:"<>|]', '', title)
    return title, safe_title


def extract_main_content(driver: webdriver.Chrome) -> BeautifulSoup:
    """본문 HTML 파싱 및 soup 반환"""
    main_content = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "se-main-container"))
    )
    soup = BeautifulSoup(main_content.get_attribute('innerHTML'), 'html.parser')
    return soup


def extract_text_and_images(soup: BeautifulSoup, translator: Any) -> Tuple[List[str], List[str], int]:
    """본문 텍스트/이미지 추출 및 번역, 마크다운 리스트 반환"""
    content_parts = []
    content_parts_en = []
    image_count = 1
    for component in soup.find_all('div', class_='se-component'):
        if 'se-text' in component.get('class', []):
            paragraphs = component.find_all('p', class_='se-text-paragraph')
            for p in paragraphs:
                text = p.get_text().strip()
                if text:
                    content_parts.append(text + '\n\n')
                    translated = translate_text(text, translator)
                    content_parts_en.append(translated + '\n\n')
        elif 'se-image' in component.get('class', []):
            img = component.find('img', class_='se-image-resource')
            if img:
                img_src = img.get('data-lazy-src') or img.get('src', '')
                if img_src:
                    img_markdown = f'\n![pic{image_count}]({img_src})\n\n'
                    content_parts.append(img_markdown)
                    content_parts_en.append(img_markdown)
                    image_count += 1
    return content_parts, content_parts_en, image_count


def generate_travel_courses(store_and_address: str, translator: Any) -> Tuple[str, str]:
    """여행 코스 추천 및 번역"""
    travel_courses = asyncio.run(add_travel(store_and_address))
    if travel_courses and not travel_courses.startswith('[ERROR]'):
        translated_courses = translate_text(travel_courses, translator)
        return travel_courses, translated_courses
    return '', ''


def crawl_naver_blog(url: str, translator: Any) -> Dict[str, Any]:
    """
    네이버 블로그 크롤러 메인 함수. 각 역할별 함수 호출로 구성.
    """
    driver = get_chrome_driver()
    try:
        driver.get(url)
        # iframe 전환
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "mainFrame"))
        )
        driver.switch_to.frame(iframe)

        # 제목 추출 및 번역
        title, safe_title = extract_blog_title(driver)
        eng_title = translate_text(title + " korea hongdae", translator)

        # 본문 파싱
        soup = extract_main_content(driver)

        # 텍스트/이미지 추출 및 번역
        content_parts, content_parts_en, image_count = extract_text_and_images(soup, translator)
        content_parts.insert(0, f"{title}\n\n")
        content_parts_en.insert(0, f"{eng_title}\n\n")

        # 매장/주소 추출
        store_and_address = extract_store_and_address(content_parts)

        print("주소 결과 값", store_and_address)
        # 여행코스 추천 및 번역
        travel_courses, translated_courses = generate_travel_courses(store_and_address, translator)
        if travel_courses:
            content_parts.append("\n# 여행 코스 추천\n\n")
            content_parts.append(travel_courses + "\n\n")
            content_parts_en.append("\n# Seoul Travel Guide Recommendation by Korean\n\n")
            content_parts_en.append(translated_courses + "\n\n")

        return {
            "url": url,
            "title": title,
            "safe_title": safe_title,
            "eng_title": eng_title,
            "content_parts": content_parts,
            "content_parts_en": content_parts_en,
            "store_and_address": store_and_address,
            "image_count": image_count,
            "travel_courses": travel_courses,
            "translated_travel_courses": translated_courses
        }
    finally:
        driver.quit()
