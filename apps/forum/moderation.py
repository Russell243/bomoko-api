from django.conf import settings

DEFAULT_BLOCKED_KEYWORDS = [
    'viol',
    'rape',
    'porn',
    'pornographie',
    'pedophile',
]

DEFAULT_FLAGGED_KEYWORDS = [
    'harcelement',
    'harcèlement',
    'chantage',
    'sexe contre points',
    'agression',
]


def moderate_forum_text(text: str):
    text_l = (text or '').lower()
    blocked_keywords = getattr(settings, 'FORUM_BLOCKED_KEYWORDS', DEFAULT_BLOCKED_KEYWORDS)
    flagged_keywords = getattr(settings, 'FORUM_FLAGGED_KEYWORDS', DEFAULT_FLAGGED_KEYWORDS)

    for keyword in blocked_keywords:
        if keyword in text_l:
            return 'blocked', f'mot_interdit:{keyword}'

    for keyword in flagged_keywords:
        if keyword in text_l:
            return 'flagged', f'revue_humaine:{keyword}'

    return 'approved', ''
