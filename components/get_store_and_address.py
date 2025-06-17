import re

def extract_store_and_address(paragraphs):
    print('주소 찾기 시작')
    store_name = None
    address = None
    print(paragraphs)

    # 1. store_name: paragraphs에서 # 뒤에 나오는 첫 단어
    for text in paragraphs:
        m = re.match(r'#\s*([^\s#]+)', text)
        if m:
            store_name = m.group(1).strip()
            break

    # 2. 주소: "◈ 위치" 다음 줄이 주소인 경우
    for idx, text in enumerate(paragraphs):
        if '위치' in text and '' in text:
            # 다음 줄이 존재하면 주소로 간주
            if idx + 1 < len(paragraphs):
                candidate = paragraphs[idx + 1].strip()
                if '구' in candidate:
                    address = candidate
                    break
        # 기존 패턴도 fallback
        m = re.search(r'(주소|위치)[:：]?\s*([^\n]+)', text)
        if m and '구' in m.group(2):
            address = m.group(2).strip()
            break
        m = re.search(r'([가-힣]+시)? ?([가-힣]+구) ?([가-힣]+동)? ?[0-9\-]+', text)
        if m:
            address = m.group(0).strip()
            break
          
    print("주소찾기 종료")
    return f"{store_name}, {address}"