import os
import re
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

    data = {
        'title': result['eng_title'],
        'content': content,
        'desc': desc,
        'image': image,
        'tags': tags
    }
    return data

from components.supabase import insert_eng_post

def process_blog_post(url: str, translator) -> bool:
    """
    단일 네이버 블로그 포스트를 크롤링, 번역, 마크다운 저장, Supabase insert까지 처리합니다.
    성공 시 True, 실패 시 False 반환.
    """
    try:
        # 1. 네이버 블로그 크롤링 및 번역 결과 dict 획득
        result = crawl_naver_blog(url, translator)

        # 2. 마크다운 파일 저장 (한글/영문)
        file_paths = save_markdown_files(
            result['content_parts'],
            result['content_parts_en'],
            result['safe_title'],
            result['eng_title']
        )

        # 3. Supabase insert용 데이터 생성
        supabase_data = make_supabase_data(result, file_paths['eng_path'], translator)
        print("\n[SupaBase Insert Data]")
        # print(supabase_data)

        # 4. Supabase engPost 테이블에 데이터 저장
        try:
            insert_result = insert_eng_post(supabase_data)
            print("[Supabase Insert 결과]", insert_result)
        except Exception as supa_err:
            print(f"[Supabase Insert 에러] {supa_err}")

        # 5. 통계 및 파일 경로 출력
        print(f"\n마크다운 파일 생성 완료")
        print(f"제목: {result['title']}")
        print(f"원본 파일: {os.path.abspath(file_paths['kor_path'])}")
        print(f"번역 파일: {os.path.abspath(file_paths['eng_path'])}")
        print(f"총 {result['image_count']-1}개의 이미지가 처리되었습니다.")
        print_statistics(result['content_parts'], result['image_count'])
        return True

    except Exception as e:
        print(f"에러 발생 (URL: {url}): {str(e)}")
        return False

def main():
    # DeepL 번역기 초기화
    translator = init_translator(os.getenv('DEEPL_API_KEY'))
    
    # 새 포스트 확인
    print("새로운 포스트 확인 중...")
    new_posts = check_new_posts()
    
    if not new_posts:
        print("처리할 새 포스트가 없습니다.")
        return
    
    print(f"\n총 {len(new_posts)}개의 새 포스트를 발견했습니다.")
    
    # 각 포스트 처리
    success_count = 0
    for post in new_posts:
        print(f"\n[처리 중] {post['title']}")
        if process_blog_post(post['url'], translator):
            success_count += 1
            
            
    
    
    # 처리 결과 요약
    print(f"\n=== 처리 완료 ===")
    print(f"총 {len(new_posts)}개 중 {success_count}개 처리 성공")
    if success_count < len(new_posts):
        print(f"실패: {len(new_posts) - success_count}개")

if __name__ == "__main__":
    main()
