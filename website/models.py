from .extensions import db
from sqlalchemy import Time,Boolean,UniqueConstraint
from flask_login import UserMixin

class Match(db.Model):
    match_id = db.Column(db.Integer, primary_key=True)
    
    
    home_team_name = db.Column(db.Integer, db.ForeignKey('team.team_name'))
    away_team_name = db.Column(db.Integer, db.ForeignKey('team.team_name'))
    league_id = db.Column(db.Integer, db.ForeignKey('league.league_id'))  
    # This line makes sure that no duplicates can be inserted
    __table_args__ = (
        UniqueConstraint('home_team_name', 'away_team_name', 'league_id', name='unique_match'),
    )
     
class Venue(db.Model):
    venue_id = db.Column(db.Integer, primary_key = True)
    venue_name = db.Column(db.String(150))
    
    venue_availability = db.Column(Boolean, default=True)
    accepts_outside_teams = db.Column(Boolean,default=True)
    
    available_time_start = db.Column(Time)
    available_time_end = db.Column(Time)

    slot_one = db.Column(Boolean,default = True)
    slot_two = db.Column(Boolean,default = True)
    slot_three = db.Column(Boolean,default = True)
    slot_four = db.Column(Boolean,default = True)
    slot_five = db.Column(Boolean,default = True)

    venue_district_id = db.Column(db.Integer, db.ForeignKey('district.district_id'))

class League(db.Model):
    league_id = db.Column(db.Integer,primary_key = True)
    league_name = db.Column(db.String(150))
    teams = db.relationship('Team', backref='league')

class District(db.Model):
    district_id = db.Column(db.Integer,primary_key = True)
    district_name = db.Column(db.String(150))
    teams = db.relationship('Team', backref='district')
    venues = db.relationship('Venue', backref='district')

class Team(db.Model):
    team_id = db.Column(db.Integer,primary_key = True)
    team_name = db.Column(db.String(150))
    team_district_id = db.Column(db.Integer, db.ForeignKey('district.district_id'))
    team_league_id = db.Column(db.Integer,db.ForeignKey('league.league_id'))  

class Admin(db.Model,UserMixin):
    admin_id = db.Column(db.Integer,primary_key = True)
    password = db.Column(db.String(150))
    user_name = db.Column(db.String(150))

