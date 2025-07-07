import os
import re
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

from components.deepl import init_translator
from components.translation_counter import get_remaining_chars, update_translation_count
from components.naver_crawler import crawl_naver_blog
from components.naver_rss import check_new_posts

def count_characters(text_list: List[str]) -> int:
    """마크다운 텍스트 리스트의 총 글자 수를 계산합니다."""
    return sum(len(text.strip()) for text in text_list 
              if not text.strip().startswith('!['))

def sanitize_filename(filename: str) -> str:
    """파일명에 사용할 수 없는 문자를 제거합니다."""
    return re.sub(r'[\\/*?:"<>|]', '', filename)

def save_markdown_files(content_parts: List[str], content_parts_en: List[str], 
                       safe_title: str, eng_title: str) -> Dict[str, str]:
    """마크다운 파일을 저장하고 파일 경로를 반환합니다."""
    # 디렉토리 생성
    kor_dir = 'kor'
    eng_dir = 'eng'
    os.makedirs(kor_dir, exist_ok=True)
    os.makedirs(eng_dir, exist_ok=True)
    
    # 파일 경로 설정 (파일명 정규화 적용)
    md_filename = f"{sanitize_filename(safe_title)}.md"
    md_filename_en = f"{sanitize_filename(eng_title)}.md"
    kor_path = os.path.join(kor_dir, md_filename)
    eng_path = os.path.join(eng_dir, md_filename_en)
    
    # 파일 저장
    with open(kor_path, 'w', encoding='utf-8') as f:
        f.writelines(content_parts)
    with open(eng_path, 'w', encoding='utf-8') as f:
        f.writelines(content_parts_en)
    
    return {
        'kor_path': kor_path,
        'eng_path': eng_path
    }

def print_statistics(content_parts: List[str], image_count: int) -> None:
    """번역 통계를 출력합니다."""
    total_chars = count_characters(content_parts)
    remaining_chars = get_remaining_chars()
    estimated_posts = remaining_chars // total_chars if total_chars > 0 else 0
    
    print("\n=== 번역 통계 ===")
    print(f"현재 글의 총 글자 수: {total_chars:,}자")
    print(f"이번 달 누적 번역: {get_remaining_chars() + total_chars:,}자")
    print(f"한 달 동안 번역 가능한 예상 글 개수: 약 {estimated_posts}개")
    print(f"남은 글자 수: {remaining_chars:,}자")

def make_supabase_data(result, eng_md_path, translator):
    # content: 영어 마크다운 전체 텍스트
    with open(eng_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # desc: 본문 앞부분 요약 후 번역
    summary = ''.join(result['content_parts'][:2]).replace('\n', ' ')
    from components.deepl import translate_text
    desc = translate_text(summary, translator)

    # image: 첫 번째 이미지 URL 추출
    image = None
    for part in result['content_parts_en']:
        if part.strip().startswith('!['):
            import re
            m = re.search(r'\((.*?)\)', part)
            if m:
                image = m.group(1)
                break

    # tags: 제목/본문에서 # 또는 [] 등으로 추출(없으면 빈 리스트)
    tags = []
    import re
    tags += re.findall(r'#([\w가-힣]+)', ''.join(result['content_parts']))
    tags += re.findall(r'\[([^\]]+)\]', result['title'])
    tags = list(set(tags))

    # 한글/영문 주소 추가
    kor_url = result.get('url')

    data = {
        'title': result['eng_title'],
        'content': content,
        'desc': desc,
        'image': image,
        'tags': tags,
        'kor_url': kor_url,
        'address': result.get('store_and_address', None)
    }
    return data

# from components.uploader import upload_markdown_to_supabase

def crawl_and_save_markdown(url: str, translator, rss_data: dict = None) -> dict:
    """
    크롤링, 번역, 마크다운 저장 및 메타정보(json) 저장만 수행
    성공 시 meta 딕셔너리를 반환, 실패 시 None 반환
    
    Args:
        url: 크롤링할 블로그 URL
        translator: 번역기 객체
        rss_data: RSS에서 추출한 추가 데이터 (선택사항)
    """
    try:
        result = crawl_naver_blog(url, translator)
        file_paths = save_markdown_files(
            result['content_parts'],
            result['content_parts_en'],
            result['safe_title'],
            result['eng_title']
        )
        
        # 메타정보를 별도 json으로 저장
        meta = {
            'title': result['eng_title'],
            'kor_title': result['title'],
            'safe_title': result['safe_title'],
            'eng_title': result['eng_title'],
            'address': result.get('store_and_address'),
            'tags': list(set(re.findall(r'#([\w가-힣]+)', ''.join(result['content_parts'])))),
            'kor_url': result.get('url'),
            'image_count': result.get('image_count'),
            'eng_md_path': file_paths['eng_path'],
            'kor_md_path': file_paths['kor_path']
        }
        
        # RSS에서 추출한 이미지 URL이 있으면 메타정보에 추가
        if rss_data and 'image_url' in rss_data and rss_data['image_url']:
            meta['image_url'] = rss_data['image_url']
            print(f"RSS에서 이미지 URL 추출됨: {rss_data['image_url']}")
        else:
            # 마크다운에서 이미지 URL 추출 시도
            markdown_content = ''.join(result['content_parts_en'])
            # 고정: 정규식 패턴 수정 (작은따옴표 제거)
            image_urls = re.findall(r'!\[.*?\]\((https?://[^\s)]+)\)', markdown_content)
            if image_urls:
                meta['image_url'] = image_urls[0]
                print(f"마크다운에서 이미지 URL 추출됨: {image_urls[0]}")
        
        meta_path = file_paths['eng_path'].replace('.md', '.meta.json')
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"[Crawling/Markdown 완료] {file_paths['eng_path']} / {meta_path}")
        return meta # 성공 시 meta 딕셔너리 반환
    except Exception as e:
        print(f"[크롤링/마크다운 저장 에러] {url}: {e}")
        return None # 실패 시 None 반환

def main():
    # DeepL 번역기 초기화
    translator = init_translator(os.getenv('DEEPL_API_KEY'))
    
    # processed_posts.json 로드 (URL 목록만 저장)
    processed_posts_path = 'processed_posts.json'
    processed_urls = set()
    if os.path.exists(processed_posts_path):
        try:
            with open(processed_posts_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 이전 버전과 호환성을 위해 리스트인지 확인
                if isinstance(data, list):
                    # 각 항목이 문자열(URL)인지 딕셔너리(이전 버전 메타)인지 확인
                    for item in data:
                        if isinstance(item, str):
                            processed_urls.add(item)
                        elif isinstance(item, dict) and 'kor_url' in item:
                            processed_urls.add(item['kor_url'])
        except json.JSONDecodeError:
            print(f"Warning: {processed_posts_path} is empty or malformed. Starting with an empty list.")
        except Exception as e:
            print(f"Error loading {processed_posts_path}: {e}")
    
    # 기존 처리된 URL 로그 출력
    print(f"이미 처리된 URL 개수: {len(processed_urls)}")
    if processed_urls:
        print("처음 5개 URL 예시:", list(processed_urls)[:5])

    # 새 포스트 확인
    print("새로운 포스트 확인 중...")
    category = "맛집일기_얌얌"
    new_posts = check_new_posts(category)
    
    if not new_posts:
        print("처리할 새 포스트가 없습니다.")
        return
    
    print(f"\n총 {len(new_posts)}개의 새 포스트를 발견했습니다.")
    
    # 각 포스트 처리
    success_count = 0
    new_processed_urls = set(processed_urls)  # 기존 URL 세트 복사
    
    for post in new_posts:
        post_url = post.get('url')
        if not post_url:
            print(f"Skipping post with no URL: {post.get('title', 'Unknown Title')}")
            continue
            
        # 이미 처리된 URL인지 확인
        if post_url in new_processed_urls:
            print(f"[건너뜀] 이미 처리된 포스트: {post['title']}")
            continue
            
        print(f"\n[처리 중] {post['title']}")
        print(f"URL: {post_url}")
        
        # RSS에서 추출한 데이터를 포함하여 crawl_and_save_markdown 호출
        meta_data = crawl_and_save_markdown(post_url, translator, rss_data=post)

        if meta_data:  # 성공적으로 처리된 경우
            success_count += 1
            new_processed_urls.add(post_url)  # 처리된 URL만 추가
            print(f"[처리 완료] {post['title']}")
        else:
            print(f"[처리 실패] {post['title']}")
            
    # 처리 결과 요약
    print(f"\n=== 처리 완료 ===")
    print(f"총 {len(new_posts)}개 중 {success_count}개 처리 성공")
    if success_count < len(new_posts):
        print(f"실패: {len(new_posts) - success_count}개")

    # 업데이트된 processed_posts.json 저장 (URL 목록만 저장)
    with open(processed_posts_path, 'w', encoding='utf-8') as f:
        # URL만 리스트로 변환하여 저장
        json.dump(sorted(list(new_processed_urls)), f, ensure_ascii=False, indent=2)
    print(f"\nprocessed_posts.json이 업데이트되었습니다. 총 {len(new_processed_urls)}개의 URL이 저장되었습니다.")
    
    # 처리 요약
    new_urls_count = len(new_processed_urls - processed_urls)
    print(f"\n=== 처리 요약 ===")
    print(f"새로 처리된 URL: {new_urls_count}")
    print(f"총 처리된 URL: {len(new_processed_urls)}")

if __name__ == "__main__":
    main()