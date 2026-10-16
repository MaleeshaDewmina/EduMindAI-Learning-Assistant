"""Phase 5 v2 draft evaluation: submission sequence, correctness, privacy, CSRF."""
from app.extensions import db
from app.models.evaluation_response import EvaluationResponse
from app.models.evaluation_item_response import EvaluationItemResponse
from app.models.user import User
from app.services.evaluation_instrument import INSTRUMENT_VERSION, SCALES, CORE_CODES, PRE_ONLY, POST_ONLY
from tests.test_auth_security import register, login, csrf


def form_data(client, path, value=4):
    extra = PRE_ONLY if path.endswith('/pre-test') else POST_ONLY
    codes = CORE_CODES + tuple(item['code'] for item in extra)
    return {'csrf_token': csrf(client, '/evaluation/'), **{code: str(value) for code in codes}}


def submit(client, path, value=4, changes=None):
    data = form_data(client, path, value)
    data.update(changes or {})
    return client.post(path, data=data, follow_redirects=True)


def test_pre_and_post_core_question_text_identical(client):
    register(client)
    login(client)
    pre = client.get('/evaluation/pre-test')
    assert pre.status_code == 200
    # Need a valid pre-test to access the post-test screen.
    submit(client, '/evaluation/pre-test')
    post = client.get('/evaluation/post-test')
    assert post.status_code == 200
    for scale in SCALES:
        for item in scale['items']:
            assert item['text'].encode('utf-8') in pre.data
            assert item['text'].encode('utf-8') in post.data
    assert b'expected usefulness' in pre.data.lower()
    assert b'ease' in post.data.lower() or b'navigate' in post.data.lower()


def test_post_requires_v2_pretest(client, app):
    register(client)
    login(client)
    res = client.get('/evaluation/post-test', follow_redirects=True)
    assert b'Complete the revised pre-test before the post-test.' in res.data
    with app.app_context():
        assert EvaluationResponse.query.count() == 0


def test_csrf_required_for_evaluation(client, app):
    register(client)
    login(client)
    data = {code: '4' for code in CORE_CODES}
    data['E1'] = '4'
    assert client.post('/evaluation/pre-test', data=data).status_code == 400
    with app.app_context():
        assert EvaluationResponse.query.count() == 0


def test_invalid_missing_and_out_of_range_items_are_rejected(client, app):
    register(client)
    login(client)
    bad = submit(client, '/evaluation/pre-test', changes={'M3': '6'})
    assert b'Please answer every question' in bad.data
    missing = submit(client, '/evaluation/pre-test', changes={'G2': ''})
    assert b'Please answer every question' in missing.data
    with app.app_context():
        assert EvaluationResponse.query.count() == 0
        assert EvaluationItemResponse.query.count() == 0


def test_comments_length_rejected(client, app):
    register(client)
    login(client)
    r = submit(client, '/evaluation/pre-test', changes={'feedback_comments': 'x' * 1001})
    assert b'must not exceed 1000' in r.data
    with app.app_context():
        assert EvaluationResponse.query.count() == 0


def test_item_responses_and_matched_means_not_rounded_legacy(client, app):
    register(client)
    login(client)
    pre = submit(client, '/evaluation/pre-test', changes={'M1': '2', 'M2': '3', 'M3': '4'})
    assert b'PreTest questionnaire submitted successfully' in pre.data
    post = submit(client, '/evaluation/post-test', changes={'M1': '3', 'M2': '4', 'M3': '5'})
    assert b'PostTest questionnaire submitted successfully' in post.data
    assert b'+1.00' in post.data
    with app.app_context():
        records = EvaluationResponse.query.order_by(EvaluationResponse.response_id).all()
        assert len(records) == 2
        assert records[0].evaluation_type == 'PreTest'
        assert records[1].evaluation_type == 'PostTest'
        assert EvaluationItemResponse.query.filter_by(response_id=records[0].response_id).count() == 10
        assert EvaluationItemResponse.query.filter_by(response_id=records[1].response_id).count() == 12
        assert EvaluationItemResponse.query.filter_by(instrument_version=INSTRUMENT_VERSION).count() == 22
        saved_pre = {x.item_code: x.rating for x in records[0].item_scores}
        saved_post = {x.item_code: x.rating for x in records[1].item_scores}
        assert [saved_pre[c] for c in ('M1', 'M2', 'M3')] == [2, 3, 4]
        assert [saved_post[c] for c in ('M1', 'M2', 'M3')] == [3, 4, 5]


def test_single_submission_per_type(client, app):
    register(client)
    login(client)
    submit(client, '/evaluation/pre-test')
    second = submit(client, '/evaluation/pre-test', value=1)
    assert b'already been submitted' in second.data
    submit(client, '/evaluation/post-test')
    again = submit(client, '/evaluation/post-test', value=1)
    assert b'already been submitted' in again.data
    with app.app_context():
        assert EvaluationResponse.query.count() == 2


def test_old_legacy_rows_not_treated_as_revised_answers(client, app):
    register(client)
    login(client)
    with app.app_context():
        user = User.query.filter_by(email='student@example.com').one()
        db.session.add(EvaluationResponse(
            user_id=user.user_id, evaluation_type='PreTest',
            motivation_rating=5, confidence_rating=4,
            growth_mindset_rating=3, usability_rating=5,
        ))
        db.session.commit()
    r = client.get('/evaluation/')
    assert b'Legacy / other questionnaire version' in r.data
    assert b'Open Pre-Test' in r.data
    submit(client, '/evaluation/pre-test')
    with app.app_context():
        assert EvaluationResponse.query.count() == 2


def test_user_cannot_view_other_users_scores(client, app):
    register(client)
    login(client)
    submit(client, '/evaluation/pre-test', value=1)
    submit(client, '/evaluation/post-test', value=5)

    other_client = app.test_client()
    register(other_client, 'other@example.com')
    login(other_client, 'other@example.com')
    page = other_client.get('/evaluation/')
    assert page.status_code == 200
    assert b'No evaluation responses yet' in page.data
    assert b'+4.00' not in page.data
    with app.app_context():
        assert EvaluationResponse.query.count() == 2


def test_evaluation_post_is_not_allowed_for_unauthenticated(client):
    assert client.get('/evaluation/pre-test').status_code == 302
    assert client.get('/evaluation/post-test').status_code == 302
