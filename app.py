import asyncio

from components.deepl import init_translator, translate_text
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


from components.get_store_and_address import extract_store_and_address
from components.add_travel import add_travel

from dotenv import load_dotenv
from components.translation_counter import get_remaining_chars, update_translation_count

# Load environment variables
load_dotenv()

import os
import re
# from pathlib import Path


def count_characters(text_list):
    total_chars = 0
    for text in text_list:
        if not text.strip().startswith('!['):
            total_chars += len(text.strip())
    return total_chars

def save_to_file(content, filename, output_dir='.'):
    """Save content to a file in the specified directory"""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the full file path
    filepath = os.path.join(output_dir, filename)
    
    # Save the content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(content)
    
    return filepath

def main():
    # 테스트용 URL
    url = 'https://blog.naver.com/dev-dev/223866688653'

    # Chrome 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 헤드리스 모드
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # DeepL 번역기 초기화
    translator = init_translator(os.getenv('DEEPL_API_KEY'))
    
    driver = webdriver.Chrome(options=chrome_options)
    try:
        print(f"크롤링 시작: {url}")
        driver.get(url)
        print("페이지 로드 완료")
        
        # iframe으로 전환
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "mainFrame"))
        )
        driver.switch_to.frame(iframe)
        print("iframe 전환 완료")
        
        # 제목 추출
        title = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "se-title-text"))
        ).text.strip()
        
        safe_title = re.sub(r'[\\/*?:"<>|]', '', title)
        eng_title = translate_text(title + "korea hongdae", translator)
        

        
        # 본문 내용 추출
        main_content = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "se-main-container"))
        )
        
        soup = BeautifulSoup(main_content.get_attribute('innerHTML'), 'html.parser')
        
        content_parts = [f"{title}\n\n"]  # Add title as markdown heading
        content_parts_en = [f"{eng_title}\n\n"]
        image_count = 1
        
        # 이미지와 텍스트 추출
        for component in soup.find_all('div', class_='se-component'):
            if 'se-text' in component.get('class', []):
                paragraphs = component.find_all('p', class_='se-text-paragraph')

                for p in paragraphs:
                    text = p.get_text().strip()

                    if text:
                        content_parts.append(text + '\n\n')

                        
                        # 번역
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
                        
        
        store_and_address = extract_store_and_address(content_parts)
        print(store_and_address) 

        # 여행 코스 추천
        travel_courses = asyncio.run(add_travel(store_and_address))
        print(travel_courses)

        # 글자 수 계산 및 업데이트
        total_chars = count_characters(content_parts)
        update_translation_count(total_chars)
        
        # 남은 글자 수 및 통계
        remaining_chars = get_remaining_chars()
        estimated_posts = remaining_chars // total_chars if total_chars > 0 else 0
        
        # 한국어 마크다운 파일 저장
        kor_dir = 'kor'
        md_filename = f"{safe_title}.md"
        save_to_file(content_parts, md_filename, kor_dir)
        
        # 영어 마크다운 파일 저장
        eng_dir = 'eng'
        md_filename_en = f"{eng_title}.md"
        save_to_file(content_parts_en, md_filename_en, eng_dir)
        
        print("\n마크다운 파일 생성 완료")
        print(f"원본 파일: {os.path.abspath(md_filename)}")
        print(f"번역 파일: {os.path.abspath(os.path.join(eng_dir, md_filename_en))}")
        print(f"총 {image_count-1}개의 이미지가 처리되었습니다.")
        print(f"\n=== 글자 수 통계 ===\n"
              f"현재 글의 총 글자 수: {total_chars:,}자\n"
              f"이번 달 누적 번역: {get_remaining_chars() + total_chars:,}자\n"
              f"한 달 동안 번역 가능한 예상 글 개수: 약 {estimated_posts}개\n"
              f"남은 글자 수: {remaining_chars:,}자")
        
    except Exception as e:
        print(f"에러 발생: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()

