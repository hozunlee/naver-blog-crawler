

import json
import re
from components.supabase import insert_eng_post

def upload_markdown_to_supabase(eng_md_path: str, meta_path: str):
    """
    eng 마크다운 파일과 메타정보(json)를 읽어 Supabase에 업로드
    """
    # 메타 정보 로드
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    # 마크다운 내용 로드
    with open(eng_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 이미지 URL 추출 (RSS description에서 가져온 image_url 우선 사용)
    image_url = meta.get('image_url')
    
    # RSS에서 이미지 URL을 찾지 못한 경우 마크다운에서 추출 시도
    if not image_url:
        image_urls = re.findall(r'!\\[.*?\\]\\((https?://[^\\s]+)\\)', content)
        image_url = image_urls[0] if image_urls else None
    
    # Supabase 데이터 생성
    data = {
        'title': meta['title'],
        'content': content,
        'desc': content[:200],  # 요약
        'image_url': image_url,  # 이미지 URL
        'tags': meta.get('tags', []),
        'kor_url': meta.get('kor_url')
    }
    
    # 주소가 있는 경우에만 추가
    if meta.get('address'):
        data['address'] = meta['address']
    try:
        insert_result = insert_eng_post(data)
        print(f"[Supabase Insert 결과] {insert_result}")
        return True, insert_result
    except Exception as supa_err:
        print(f"[Supabase Insert 에러] {supa_err}")
        return False, supa_err

