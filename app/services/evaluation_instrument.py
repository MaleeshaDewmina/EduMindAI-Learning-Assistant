"""EduMind AI pilot evaluation instrument, version 2.

These are project-written exploratory items, NOT an established validated scale.
Obtain supervisor/institutional ethics and instrument approval before participants use them.
Paired items have identical wording for pre- and post-test.
"""

INSTRUMENT_VERSION = 'v2-draft'

SCALES = (
    {
        'name': 'Motivation', 'key': 'motivation',
        'description': 'Study initiation, effort and persistence',
        'items': (
            {'code': 'M1', 'text': 'I can motivate myself to start an academic task, even when it feels difficult.'},
            {'code': 'M2', 'text': 'I make an effort to complete the study tasks I plan.'},
            {'code': 'M3', 'text': 'I stay engaged with studying when I encounter obstacles.'},
        ),
    },
    {
        'name': 'Learning confidence', 'key': 'confidence',
        'description': 'Confidence in studying and handling difficulties',
        'items': (
            {'code': 'C1', 'text': 'I feel confident organising my study tasks.'},
            {'code': 'C2', 'text': 'I feel confident finding a way forward when I struggle with studying.'},
            {'code': 'C3', 'text': 'I can improve the way I study when a strategy does not work.'},
        ),
    },
    {
        'name': 'Growth-mindset-oriented beliefs', 'key': 'growth_mindset',
        'description': 'Beliefs about improvement, feedback and challenges',
        'items': (
            {'code': 'G1', 'text': 'I believe my academic abilities can develop through learning and practice.'},
            {'code': 'G2', 'text': 'When I make a mistake in my studies, I can use feedback to improve.'},
            {'code': 'G3', 'text': 'Facing a challenging academic task can help me learn.'},
        ),
    },
)

PRE_ONLY = (
    {'code': 'E1', 'text': 'I expect a learning assistant combining planning and AI support could be useful for organising my studies.'},
)

POST_ONLY = (
    {'code': 'U1', 'text': 'EduMind AI was easy for me to navigate.'},
    {'code': 'U2', 'text': 'The personalised feedback from EduMind AI was relevant to my recorded study activity.'},
    {'code': 'U3', 'text': 'EduMind AI helped me organise my study tasks.'},
)

CORE_CODES = tuple(item['code'] for scale in SCALES for item in scale['items'])


def required_items(evaluation_type):
    if evaluation_type not in ('PreTest', 'PostTest'):
        raise ValueError('Unexpected evaluation type')
    extra = PRE_ONLY if evaluation_type == 'PreTest' else POST_ONLY
    return [item for scale in SCALES for item in scale['items']] + list(extra)


def scale_score(scores, scale):
    codes = [item['code'] for item in scale['items']]
    if not all(code in scores for code in codes):
        return None
    return round(sum(scores[code] for code in codes) / len(codes), 2)


def score_summary(scores):
    return {scale['key']: scale_score(scores, scale) for scale in SCALES}
