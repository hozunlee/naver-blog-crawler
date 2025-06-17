import os

COUNTER_FILE = 'translation_counter.txt'

def get_translation_count():
    if not os.path.exists(COUNTER_FILE):
        return 0
    try:
        with open(COUNTER_FILE, 'r') as f:
            return int(f.read().strip() or 0)
    except (ValueError, IOError):
        return 0

def update_translation_count(chars_count):
    current = get_translation_count()
    with open(COUNTER_FILE, 'w') as f:
        f.write(str(current + chars_count))

def get_remaining_chars():
    monthly_limit = 493989  # DeepL 무료 티어 월간 제한
    return max(0, monthly_limit - get_translation_count())
