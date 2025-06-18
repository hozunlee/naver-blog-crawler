# Naver Blog Travel Crawler

[🇺🇸 English Version Below](#naver-blog-travel-crawler-1)

네이버 블로그에서 여행/맛집 포스팅을 자동으로 크롤링하여,

-   **가게명 및 상세 주소 추출**
-   **DeepL 번역 및 번역량 누적 관리**
-   **Perplexity LLM 기반 여행코스 자동 추천**
-   **이미지 포함 마크다운 파일 생성 (한글/영문)**
    까지 한 번에 처리하는 AI 기반 여행 콘텐츠 자동화 솔루션입니다.

## 🚀 주요 기능

-   **블로그 본문 크롤링**: 네이버 블로그의 본문 및 이미지를 자동 추출
-   **가게명/상세주소 추출**: 포스트 내에서 가게명(헤더)과 실제 주소(위치/주소 패턴) 자동 인식
-   **여행코스 자동 추천**: 추출된 주소를 기반으로 Perplexity LLM이 3가지 테마의 여행코스 추천
-   **자동 번역 시스템**: DeepL을 활용한 자동 번역 및 번역량 자동 관리
-   **이미지 통합 관리**: 원본 이미지 다운로드 및 마크다운 내 자동 참조
-   **번역 통계 대시보드**: 실시간 번역량 추적 및 잔여 할당량 표시

## 전체 기술 흐름(아키텍처)

```
[Naver Blog RSS] → [크롤링/파싱] → [DeepL 번역] → [여행코스 추천(LLM 기반)] → [마크다운 저장] → [Supabase 업로드]
```

### 1. 새 글 감지

-   `naver_rss.py`에서 RSS 피드를 주기적으로 확인, 새로운 포스트 URL 목록을 수집합니다.

### 2. 크롤링/파싱

-   `naver_crawler.py`에서 Selenium과 BeautifulSoup으로 본문, 이미지, 주소, 태그 등 주요 정보를 추출합니다.
-   주소/매장 정보는 별도 로직(`get_store_and_address.py`)으로 정교하게 추출합니다.

### 3. 번역

-   DeepL API를 활용해 제목, 본문, 요약, 태그를 영어로 번역합니다.
-   번역량(글자수) 통계를 자동으로 관리합니다.

### 4. 마크다운 파일 저장

-   한글/영문 각각 Markdown 파일로 저장합니다.
-   파일명은 안전하게 정규화(sanitize) 처리되어 에러 없이 저장됩니다.

### 5. Supabase 업로드

-   영문 포스트 데이터(제목, 본문, 요약, 대표이미지, 태그)를 `supabase.py`를 통해 engPost 테이블에 insert합니다.
-   업로드 성공/실패는 상세 로그로 확인할 수 있습니다.

### 환경 변수 설정 (`.env` 파일 생성):

    ```env
    DEEPL_API_KEY=your_deepl_api_key
    SUPABASE_URL=your_supabase_url
    SUPABASE_KEY=your_supabase_key
    RSS_URL=your_rss_url
    ```

3. ChromeDriver 설치:
    - [ChromeDriver 다운로드](https://chromedriver.chromium.org/downloads)
    - 시스템 PATH에 추가하거나 프로젝트 루트에 배치

## 주요 로직 스택

-   **Selenium/BeautifulSoup**: 동적 웹 크롤링/HTML 파싱
-   **feedparser**: RSS 피드 파싱
-   **DeepL API**: 자연어 번역
-   **supabase-py**: Supabase DB 연동
-   **python-dotenv**: 환경변수 관리
-   **pytest**: 테스트 자동화

## 🚀 사용 방법

```bash
poetry install

# 기본 실행
poetry run python app.py
```

## 📂 출력 결과

```
├── [원본_블로그_제목].md # 한국어 원본
├── eng/
│ └── [영문_제목].md # 영문 번역본
└── images/ # 다운로드된 이미지들

```

## 📊 번역 통계

```

=== 글자 수 통계 ===
현재 글의 총 글자 수: 1,258자
이번 달 누적 번역: 502,258자
한 달 동안 번역 가능한 예상 글 개수: 약 397개
남은 글자 수: 497,742자

```

## 이렇게 쓰면 좋아요!

-   여행/맛집 블로그 자동 영문화 및 글로벌 확산
-   데이터 분석/추천 서비스의 입력 데이터 자동화
-   반복적 컨텐츠 변환 및 DB 적재 업무 완전 자동화

## 🌟 비즈니스 가치

-   **콘텐츠 크리에이터**: 다국어 블로그 운영 자동화
-   **여행 플랫폼**: 실제 방문객 리뷰 기반의 신뢰도 높은 여행코스 제공
-   **로컬 비즈니스**: 지역 기반 타겟 마케팅에 활용

---

# Naver Blog Travel Crawler

An AI-powered automation tool that crawls Naver Blog travel/food posts and:

-   Extracts store names and detailed addresses
-   Translates content via DeepL with quota tracking
-   Generates travel itineraries using Perplexity LLM
-   Saves markdown files (Korean/English) with images

## 🚀 Key Features

-   **Blog Content Crawling**: Extracts text and images from Naver Blog
-   **Store/Address Extraction**: Auto-detects store names and addresses
-   **AI Travel Itineraries**: Generates 3 themed travel courses
-   **Auto-Translation**: DeepL integration with quota management
-   **Image Handling**: Downloads and embeds images in markdown
-   **Translation Dashboard**: Real-time quota tracking

## 🛠 Installation

```bash
poetry install
cp .env.example .env  # Add your API keys
```

## 🚀 Usage

```bash
poetry run python app.py
```

## 📂 Output Structure

```
.
├── [Original_Title].md          # Korean original
├── eng/
│   └── [English_Title].md       # English translation
└── images/                      # Downloaded images
```

## 📊 Translation Stats

```
=== Character Count ===
Current post: 1,258 chars
Monthly total: 502,258 chars
Estimated posts left: ~397
Remaining quota: 497,742 chars
```

## 📝 License

MIT Licensed

## Usage

1. Open `app.py` and update the target URL:

    ```python
    # 테스트용 URL
    url = 'https://blog.naver.com/dev-dev/223666008359'  # Replace with your target Naver Blog URL
    ```

2. (Optional) To enable translation:

    - Uncomment the translation-related code in `app.py`
    - Sign up for a DeepL API key at [DeepL](https://www.deepl.com/pro-api)
    - Replace `your-api-key-here` with your actual API key

3. Run the script:

    ```bash
    python app.py
    ```

4. The script will:
    - Open a Chrome browser window
    - Navigate to the specified Naver Blog post
    - Extract the title and content
    - Download and process images
    - Save the content as a markdown file with the blog post title

## Output

The script will generate a markdown file named `[Blog Post Title].md` in the same directory. The file will include:

-   The blog post title as a heading
-   Formatted text content
-   Embedded images with proper markdown syntax

## Character Count Statistics

The script provides useful statistics:

-   Total character count of the extracted text
-   Monthly character limit for DeepL free tier (500,000 characters)
-   Estimated number of posts that can be translated within the monthly limit
-   Remaining character count after processing

## Notes

-   The script is configured to work with Naver Blog's structure as of the last update
-   Some blogs might have different structures that could require adjustments to the selectors
-   Be mindful of Naver's terms of service when scraping content
-   The translation feature is currently disabled by default

## License

This project is open source and available under the [MIT License](LICENSE).
