import deepl

def init_translator(API_KEY):
    return deepl.Translator(API_KEY)

MAX_RETRIES = 3  # 최대 재시도 횟수

def translate_text(text, translator, target_lang="EN-US"):
    """
    Translate text using DeepL API
    
    Args:
        text (str): Text to translate
        translator: DeepL translator instance
        target_lang (str): Target language code (default: EN-US)
    
    Returns:
        str: Translated text or original text if translation fails
    """
    if not text.strip():
        return text
        
    retries = 0
    while retries < MAX_RETRIES:
        try:
            result = translator.translate_text(text, target_lang=target_lang)
            return result.text
        except Exception as e:
            print(f"번역 중 에러 발생 (시도 {retries + 1}/{MAX_RETRIES}): {str(e)}")
            retries += 1
    
    print(f"번역 실패 - 원본 텍스트 사용: {text[:50]}...")
    return text