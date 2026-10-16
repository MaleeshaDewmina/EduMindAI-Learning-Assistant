"""Student evaluation workflow; draft v2 instrument subject to supervisor approval."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models.evaluation_response import EvaluationResponse
from app.models.evaluation_item_response import EvaluationItemResponse
from app.models.activity_log import UserActivityLog
from app.services.evaluation_instrument import (
    INSTRUMENT_VERSION, SCALES, PRE_ONLY, POST_ONLY, CORE_CODES,
    required_items, score_summary,
)


evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/evaluation')


def current_version_response(user_id, kind):
    """Only v2 responses have item code M1; never mistake legacy rows for v2."""
    return (
        EvaluationResponse.query.join(EvaluationItemResponse)
        .filter(
            EvaluationResponse.user_id == user_id,
            EvaluationResponse.evaluation_type == kind,
            EvaluationItemResponse.item_code == 'M1',
            EvaluationItemResponse.instrument_version == INSTRUMENT_VERSION,
        )
        .order_by(EvaluationResponse.submitted_at.desc(), EvaluationResponse.response_id.desc())
        .first()
    )


def response_scores(response):
    return {item.item_code: item.rating for item in response.item_scores} if response else {}


def comparison(pre, post):
    pre_scores = score_summary(response_scores(pre)) if pre else None
    post_scores = score_summary(response_scores(post)) if post else None
    rows = []
    for scale in SCALES:
        key = scale['key']
        baseline = pre_scores[key] if pre_scores else None
        follow_up = post_scores[key] if post_scores else None
        rows.append({
            'name': scale['name'],
            'pre': baseline,
            'post': follow_up,
            'change': round(follow_up - baseline, 2)
            if baseline is not None and follow_up is not None else None,
        })
    return rows


@evaluation_bp.route('/')
@login_required
def index():
    user_id = current_user.user_id
    responses = (
        EvaluationResponse.query.filter_by(user_id=user_id)
        .order_by(EvaluationResponse.submitted_at.desc(), EvaluationResponse.response_id.desc())
        .all()
    )
    pre_test = current_version_response(user_id, 'PreTest')
    post_test = current_version_response(user_id, 'PostTest')
    return render_template(
        'evaluation/index.html',
        pre_test=pre_test,
        post_test=post_test,
        responses=responses,
        comparison=comparison(pre_test, post_test),
        pre_expectation=response_scores(pre_test).get('E1'),
        post_usability={key: response_scores(post_test).get(key) for key in ('U1', 'U2', 'U3')},
        instrument_version=INSTRUMENT_VERSION,
    )


@evaluation_bp.route('/pre-test', methods=['GET', 'POST'])
@login_required
def pre_test():
    return handle_evaluation_form('PreTest')


@evaluation_bp.route('/post-test', methods=['GET', 'POST'])
@login_required
def post_test():
    return handle_evaluation_form('PostTest')


def handle_evaluation_form(evaluation_type):
    user_id = current_user.user_id
    existing = current_version_response(user_id, evaluation_type)
    if existing is not None:
        flash('This version of the questionnaire has already been submitted for your account.', 'info')
        return redirect(url_for('evaluation.index'))

    if evaluation_type == 'PostTest' and current_version_response(user_id, 'PreTest') is None:
        flash('Complete the revised pre-test before the post-test.', 'warning')
        return redirect(url_for('evaluation.index'))

    items = required_items(evaluation_type)
    if request.method == 'POST':
        scores = {}
        for item in items:
            raw = request.form.get(item['code'])
            try:
                value = int(raw) if raw is not None else None
            except (TypeError, ValueError):
                value = None
            if value not in (1, 2, 3, 4, 5):
                flash('Please answer every question using a rating from 1 to 5.', 'danger')
                return render_template(
                    'evaluation/form.html', evaluation_type=evaluation_type,
                    scales=SCALES, extra_items=PRE_ONLY if evaluation_type == 'PreTest' else POST_ONLY,
                    instrument_version=INSTRUMENT_VERSION,
                ), 400
            scores[item['code']] = value

        comments = request.form.get('feedback_comments', '').strip()
        if len(comments) > 1000:
            flash('Additional comments must not exceed 1000 characters.', 'danger')
            return redirect(request.url)

        means = score_summary(scores)
        # Keep existing non-null integer columns for backwards compatibility.
        # Exact v2 item scores remain in evaluation_item_responses; do NOT
        # use the rounded legacy integers for pre/post research comparisons.
        legacy_expectation_or_usability = (
            scores['E1'] if evaluation_type == 'PreTest' else scores['U1']
        )
        response = EvaluationResponse(
            user_id=user_id,
            evaluation_type=evaluation_type,
            motivation_rating=round(means['motivation']),
            confidence_rating=round(means['confidence']),
            growth_mindset_rating=round(means['growth_mindset']),
            usability_rating=legacy_expectation_or_usability,
            feedback_comments=comments or None,
        )
        try:
            db.session.add(response)
            db.session.flush()
            for code, value in scores.items():
                db.session.add(EvaluationItemResponse(
                    response_id=response.response_id,
                    item_code=code,
                    instrument_version=INSTRUMENT_VERSION,
                    rating=value,
                ))
            # Write activity atomically so a logging failure cannot turn a
            # successfully saved response into a misleading HTTP 500.
            db.session.add(UserActivityLog(
                user_id=user_id,
                activity_name='Evaluation Submitted',
                activity_details=f'Submitted {evaluation_type} questionnaire ({INSTRUMENT_VERSION}).',
            ))
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception('Evaluation submission failed')
            flash('Unable to save the questionnaire. Please try again later.', 'danger')
            return redirect(request.url)

        flash(f'{evaluation_type} questionnaire submitted successfully.', 'success')
        return redirect(url_for('evaluation.index'))

    return render_template(
        'evaluation/form.html', evaluation_type=evaluation_type,
        scales=SCALES, extra_items=PRE_ONLY if evaluation_type == 'PreTest' else POST_ONLY,
        instrument_version=INSTRUMENT_VERSION,
    )
