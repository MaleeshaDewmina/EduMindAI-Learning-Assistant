"""Stores item-level pilot questionnaire answers without changing old response rows."""
from app.extensions import db


class EvaluationItemResponse(db.Model):
    __tablename__ = 'evaluation_item_responses'

    item_response_id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(
        db.Integer,
        db.ForeignKey('evaluation_responses.response_id'),
        nullable=False,
        index=True,
    )
    item_code = db.Column(db.String(12), nullable=False)
    instrument_version = db.Column(db.String(24), nullable=False)
    rating = db.Column(db.Integer, nullable=False)

    response = db.relationship(
        'EvaluationResponse',
        backref=db.backref('item_scores', lazy='select', cascade='all, delete-orphan'),
    )

    __table_args__ = (
        db.UniqueConstraint('response_id', 'item_code', name='uq_eval_response_item'),
    )
