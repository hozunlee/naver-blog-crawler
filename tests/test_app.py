import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from unittest.mock import patch, MagicMock
from app import count_characters, save_markdown_files, process_blog_post

@pytest.fixture
def sample_content():
    return [
        "제목입니다\n\n",
        "본문 내용입니다.\n\n",
        "![pic1](http://image.url)\n\n"
    ]

def test_count_characters(sample_content):
    # 이미지 마크다운 제외, 텍스트만 글자수 합산
    assert count_characters(sample_content) == len("제목입니다") + len("본문 내용입니다.")

def test_save_markdown_files(tmp_path, sample_content):
    kor = sample_content
    eng = ["Title\n\n", "Body content.\n\n", "![pic1](http://image.url)\n\n"]
    safe_title = "테스트제목"
    eng_title = "TestTitle"
    # 임시 디렉토리로 경로 변경
    with patch("app.os.makedirs") as makedirs:
        paths = save_markdown_files(kor, eng, safe_title, eng_title)
        assert 'kor_path' in paths and 'eng_path' in paths
        assert paths['kor_path'].endswith(f"{safe_title}.md")
        assert paths['eng_path'].endswith(f"{eng_title}.md")

@patch("app.crawl_naver_blog")
def test_process_blog_post_success(mock_crawl):
    # 크롤러가 dict를 정상 반환하는 경우
    mock_crawl.return_value = {
        'content_parts': ["제목\n\n", "본문\n\n"],
        'content_parts_en': ["Title\n\n", "Body\n\n"],
        'safe_title': "제목",
        'eng_title': "Title",
        'title': "제목",
        'image_count': 2
    }
    # 번역기 객체도 mock
    translator = MagicMock()
    assert process_blog_post("http://test.url", translator) is True

@patch("app.crawl_naver_blog")
def test_process_blog_post_fail(mock_crawl):
    # 크롤러가 예외 발생 시
    mock_crawl.side_effect = Exception("크롤링 실패")
    translator = MagicMock()
    assert process_blog_post("http://fail.url", translator) is False

def test_save_markdown_files_invalid_filename():
    kor = ["테스트\n\n"]
    eng = ["Test\n\n"]
    unsafe_title = "테스트/제목:불가?*<>|"
    unsafe_eng_title = "Test/Title:Invalid?*<>|"
    # 파일명에 불가문자 포함 시 OSError가 발생해야 함
    try:
        save_markdown_files(kor, eng, unsafe_title, unsafe_eng_title)
        assert False, "파일명에 불가문자가 포함되어 있는데 예외가 발생하지 않음"
    except OSError:
        pass  # 정상적으로 예외 발생

def test_make_supabase_data_tags_always_list(tmp_path):
    from app import make_supabase_data
    eng_md_path = tmp_path / "test_eng.md"
    eng_md_path.write_text("Test content\nSecond line\n", encoding="utf-8")

    class DummyTranslator:
        def __call__(self, *a, **kw): return "summary"
    dummy_translator = DummyTranslator()

    # tags가 없는 경우
    result1 = {
        'eng_title': 'Test Title',
        'content_parts': ["본문1\n", "본문2\n"],
        'content_parts_en': ["Title\n", "Body\n"],
        'safe_title': 'TestTitle',
        'eng_title': 'Test Title',
        'title': 'Test Title',
        'image_count': 1
    }
    data1 = make_supabase_data(result1, str(eng_md_path), dummy_translator)
    assert isinstance(data1['tags'], list)
    assert data1['tags'] == []

    # tags가 본문/제목에서 추출되는 경우
    result2 = {
        'eng_title': 'Test Title',
        'content_parts': ["#맛집 본문1\n", "[연남] 본문2\n"],
        'content_parts_en': ["Title\n", "Body\n"],
        'safe_title': 'TestTitle',
        'eng_title': 'Test Title',
        'title': '[연남] Test Title',
        'image_count': 1
    }
    data2 = make_supabase_data(result2, str(eng_md_path), dummy_translator)
    assert isinstance(data2['tags'], list)
    assert set(data2['tags']) & {"맛집", "연남"}
    print("data1:", data1)
    print("data2:", data2)
