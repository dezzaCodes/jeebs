from .. import db

class Booking(db.Model):
    """ Booking Model for storing booking related details """
    __tablename__ = "booking"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_time = db.Column(db.DateTime, nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'))
    clinic = db.relationship('Clinic', backref='booking')
    examination_id = db.Column(db.Integer, db.ForeignKey('examination.id'))
    examination = db.relationship('Examination', backref='booking')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', foreign_keys=[user_id])
    radiologist_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    radiologist = db.relationship('Employee', foreign_keys=[radiologist_id])
    confirmed = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return "<Booking '{}'>".format(self.id)