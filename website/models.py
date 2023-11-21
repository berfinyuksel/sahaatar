from . import db
from flask_login import UserMixin

class District(db.Model):
    district_id = db.Column(db.Integer,primary_key = True)
    district_name = db.Column(db.String(150))
    teams = db.relationship('Team')

class Team(db.Model):
    team_id = db.Column(db.Integer,primary_key = True)
    team_name = db.Column(db.String(150))
    team_district = db.Column(db.Integer, db.ForeignKey('district.district_id'))    

class Admin(db.Model,UserMixin):
    admin_id = db.Column(db.Integer,primary_key = True)
    password = db.Column(db.String(150))
    user_name = db.Column(db.String(150))