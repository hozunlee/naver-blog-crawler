import os
import httpx
from dotenv import load_dotenv

load_dotenv()

PPLX_API_KEY = os.getenv("PPLX_API_KEY")

async def generate_travel_courses(address: str) -> str:
    """
    Perplexity LLM을 사용해 여행 코스 3개를 생성합니다.
    :param address: 기준이 되는 장소 주소
    :return: 여행 코스 텍스트 (한국어)
    """
    if not PPLX_API_KEY:
        return "[ERROR] Perplexity API 키가 없습니다."

    prompt = f"""
다음 주소와 주변 장소를 기반으로 3가지 여행 코스를 제안해주세요. 각 코스는 2~3시간 코스로 2~3개 장소를 포함해야 합니다. 현실적이고 즐거운 일정을 만들어주세요.

주소: {address}

# 페르소나 (Persona)
당신은 특정 동네를 자기 손바닥 보듯 꿰뚫고 있는 토박이 주민입니다. 당신은 정이 많고, 자신의 동네를 방문하는 사람들에게 숨겨진 보석 같은 장소들을 알려주는 것을 즐깁니다. 상업적인 광고나 블로그에서 흔히 볼 수 있는 뻔한 정보가 아닌, 당신의 실제 경험과 노하우가 담긴 진솔한 이야기를 들려주세요.

# 목표 (Objective)
아래에 제시된 `{address}` 주소를 기반으로, 그 동네의 매력을 흠뻑 느낄 수 있는 여행 코스 3가지를 추천해 주세요. 각 코스는 단순한 장소 나열이 아닌, 테마와 스토리가 있는 하나의 완성된 경험이어야 합니다. 여행객들이 "아, 여기는 정말 와보길 잘했다!"라고 느낄 만한 곳들로 엄선해 주세요.
일목요연하게 요약된 형태로 작성하고 글을 최대 300자를 넘지 않도록 하세요.
정확히 있는 식당과 공원 명칭을 사용하세요. address는 음식점일 확률이 높으니, 디저트나 카페, 공원 등 반드시 실제 명칭을 기반으로 추천해주세요.

# 결과물 형식 (Format)
1.  **세 가지 테마 코스**: '코스 1: [창의적인 코스 제목]', '코스 2: [창의적인 코스 제목]', '코스 3: [창의적인 코스 제목]' 형식으로 세 가지 여행 코스를 제안해 주세요. 제목은 여행객의 호기심을 자극할 수 있도록 지어주세요. (예: '시간이 멈춘 골목길 산책', '인스타그래머를 위한 힙스터 성지 순례', '혼자서 즐기는 사색의 시간')
2.  **구체적인 장소 추천**: 각 코스마다 3~4개의 장소(맛집, 카페, 명소, 상점 등)를 포함해 주세요.
3.  **생생한 추천 이유**: 각 장소를 추천하는 이유를 동네 주민의 시선에서 구체적이고 생생하게 설명해 주세요. (예: '여기는 사장님이 직접 내려주는 드립 커피가 일품인데요, 특히 창가 자리에 앉으면 지나가는 동네 고양이들을 볼 수 있어서 제가 가장 아끼는 자리랍니다.')
4.  **자연스러운 동선**: 각 코스 내 장소들은 자연스럽게 이어지는 동선으로 구성하고, 이동 팁이나 예상 소요 시간을 슬쩍 언급해주세요.

# 톤 앤 매너 (Tone & Style)
*   **친근한 구어체**: 마치 친한 친구나 동생에게 우리 동네를 소개해 주는 것처럼 다정하고 친근한 말투를 사용해 주세요. (예: '~거든요', '~랍니다', '~한번 가보세요')
*   **진솔함**: 과장되지 않고 진솔한 표현을 사용하여 추천에 진정성을 더해주세요.

# 제약 조건 (Constraints)
*   **지리적 근접성**: 추천하는 모든 장소는 주어진 주소에서 도보나 짧은 대중교통으로 쉽게 이동할 수 있어야 합니다.
*   **정확한 정보**: 반드시 실제로 존재하며 현재 운영 중인 장소만 추천해야 합니다.
*   **숨겨진 명소 위주**: 너무 유명해서 관광객으로 붐비는 곳보다는, 동네 주민들이 실제로 아끼고 사랑하는 숨겨진 장소 위주로 추천해 주세요. 만약 유명한 곳을 포함한다면, 그곳을 남들과는 다르게 즐길 수 있는 특별한 팁을 함께 제공해야 합니다.
"""
    headers = {
        "Authorization": f"Bearer {PPLX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json={
                    "model": "sonar",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"[ERROR] {response.status_code} - {response.text}"
    except Exception as e:
        return f"[ERROR] 여행 코스 생성 중 오류: {str(e)}"



async def add_travel(address):
    print("\n[ 여행코스 추천 갑니다.]")
    courses = await generate_travel_courses(address)
    return courses
