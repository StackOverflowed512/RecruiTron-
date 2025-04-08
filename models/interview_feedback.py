from datetime import datetime
from .database import db

class InterviewFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    technical_score = db.Column(db.Float)
    communication_score = db.Column(db.Float)
    confidence_score = db.Column(db.Float)
    total_score = db.Column(db.Float)
    strengths = db.Column(db.JSON)
    improvements = db.Column(db.JSON)
    recommendations = db.Column(db.JSON)
    role = db.Column(db.String(100))
    
    user = db.relationship('User', backref=db.backref('interviews', lazy=True))