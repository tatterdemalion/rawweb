from datetime import datetime

from rawweb import db


class Photo(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    photographer_id = db.Column(db.Integer, db.ForeignKey('photographer.id'))
    taken_at = db.Column(db.DateTime)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow())
    size = db.Column(db.String(120))
    exif = db.Column(db.Text, default=False)

    def __repr__(self):
        return '<Photo %r>' % self.id


class Photographer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))

    def __repr__(self):
        return '<Photographer %r>' % self.name

    @property
    def serialize(self):
        return {'id': self.id, 'name': self.name}
