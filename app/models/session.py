from app import db
from datetime import datetime, timedelta


class Session(db.Model):
    __tablename__ = 'sessions'

    session_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    expires_at = db.Column(db.DateTime, nullable=False)

    @staticmethod
    def create_session(user_id, token, ip, user_agent, days=7):
        expires_at = datetime.utcnow() + timedelta(days=days)
        return Session(
            user_id=user_id,
            token=token,
            ip_address=ip,
            user_agent=user_agent,
            expires_at=expires_at
        )