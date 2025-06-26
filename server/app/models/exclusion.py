from app.extensions import db

class Exclusion(db.Model):
    __tablename__ = 'exclusions'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # 'PHONE' or 'MAC'
    value = db.Column(db.String(50), nullable=False, unique=True)  # Phone number or MAC address
    reason = db.Column(db.String(200), nullable=True)
    exclude_from_payment = db.Column(db.Boolean, default=False)  # Exempt from paying
    exclude_from_connection = db.Column(db.Boolean, default=False)  # Block from connecting

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'value': self.value,
            'reason': self.reason,
            'exclude_from_payment': self.exclude_from_payment,
            'exclude_from_connection': self.exclude_from_connection
        }
        