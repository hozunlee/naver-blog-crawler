import feedparser
import json
import os
from bs4 import BeautifulSoup

def load_processed_posts():
    """처리된 포스트 목록 불러오기"""
    if os.path.exists('processed_posts.json'):
        with open('processed_posts.json', 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_processed_posts(posts):
    """처리된 포스트 목록 저장하기"""
    with open('processed_posts.json', 'w', encoding='utf-8') as f:
        json.dump(list(posts), f, ensure_ascii=False, indent=2)

def extract_image_from_description(description: str) -> str:
    """Extract the first image URL from HTML description using BeautifulSoup"""
    if not description:
        return None
    
    try:
        soup = BeautifulSoup(description, 'html.parser')
        img_tag = soup.find('img')
        if img_tag and 'src' in img_tag.attrs:
            return img_tag['src']
    except Exception as e:
        print(f"이미지 추출 중 오류 발생: {e}")
    return None

def check_new_posts(category):
    """새로운 포스트 확인"""
    # 기존에 처리한 포스트 불러오기
    processed_posts = load_processed_posts()
    new_posts = []
    
    # 네이버 RSS 피드 파싱
    feed_url = os.getenv('RSS_URL')
    print(f"RSS 피드 확인 중: {feed_url}")
    
    try:
        feed = feedparser.parse(feed_url)
        print(f"총 {len(feed.entries)}개의 포스트를 찾았습니다.")
        
        for entry in feed.entries:
            # 원하는 카테고리인지 확인
            if any(category in tag.term for tag in entry.get('tags', [])):
                post_url = entry.link
                
                if post_url not in processed_posts:
                    # Extract image URL using BeautifulSoup
                    image_url = extract_image_from_description(entry.get('description', ''))
                    
                    post_info = {
                        'title': entry.title,
                        'url': post_url,
                        'published': entry.published,
                        'summary': entry.get('description', '')[:100] + '...',  # 요약만 표시
                        'image_url': image_url,  # Extract first image URL from description
                        'tags': entry.get('tags', [{'term': ''}])[0].term.split(',')
                    }
                    new_posts.append(post_info)
                    print(f"새 포스트 발견: {entry.title}")
        
        # 새 포스트가 있으면 저장
        if new_posts:
            new_urls = {post['url'] for post in new_posts}
            save_processed_posts(processed_posts.union(new_urls))
            print(f"총 {len(new_posts)}개의 새 포스트를 저장했습니다.")
        else:
            print("새로운 포스트가 없습니다.")
            
        return new_posts
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return []

def main():
    print("=== 네이버 블로그 새 포스트 체크 ===")
    new_posts = check_new_posts()
    
    if new_posts:
        print(new_posts )
        print("\n새로운 포스트 목록:")
        for i, post in enumerate(new_posts, 1):
            print(f"\n{i}. 제목: {post['title']}")
            print(f"   URL: {post['url']}")
            print(f"   발행일: {post['published']}")
            print(f"   요약: {post['summary']}")
            print(f"   이미지: {post['image']}")
            print(f"   태그: {post['tags']}")

if __name__ == "__main__":
    main()