import os
from supabase import create_client, Client


from dotenv import load_dotenv

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

supabase: Client = create_client(url, key)

def insert_eng_post(data: dict) -> dict:
    """
    engPost 테이블에 데이터 삽입
    :param data: {
        'title': str,
        'content': str,
        'desc': str,
        'image': str,
        'tags': list[str]
    }
    :return: Supabase 응답(dict)
    """
    # tags 컬럼이 JSONB라면 그대로, 문자열이면 ','.join(tags)로 변환 필요
    response = supabase.table("engPost").insert(data).execute()
    if hasattr(response, 'data'):
        return response.data
    return response