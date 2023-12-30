from .extensions import db
from sqlalchemy import Time,Boolean,UniqueConstraint,Date
from flask_login import UserMixin

class Match(db.Model):
    match_id = db.Column(db.Integer, primary_key=True)
    
    
    home_team_name = db.Column(db.Integer, db.ForeignKey('team.team_name'))
    away_team_name = db.Column(db.Integer, db.ForeignKey('team.team_name'))
    league_id = db.Column(db.Integer, db.ForeignKey('league.league_id'))  
    # Eğer sadece tek bir attribute farklı olacaksa neden Match ve AssignedMatch ayrı Entity? 
    # İleride tek Entity ile çözmeyi deneyelim
    match_day = db.Column(db.String(50))  
    match_slot = db.Column(db.String(50))
    match_date = db.Column(Date)
    # This line makes sure that no duplicates can be inserted
    __table_args__ = (
        UniqueConstraint('home_team_name', 'away_team_name', 'league_id','match_slot','match_date', name='unique_match'),
    )
class AssignedMatch(db.Model):
    assigned_match_id = db.Column(db.Integer, primary_key=True)
    
    home_team_name = db.Column(db.Integer, db.ForeignKey('team.team_name'))
    away_team_name = db.Column(db.Integer, db.ForeignKey('team.team_name'))
    league_id = db.Column(db.Integer, db.ForeignKey('league.league_id'))

    match_venue = db.Column(db.Integer,db.ForeignKey('venue.venue_name'), default = "Cebeci Sahasi")
    match_day = db.Column(db.String(50))  
    match_slot = db.Column(db.String(50))
    match_date = db.Column(Date)
    match_week = db.Column(db.String(50), default = "DUNNO")
    # This line makes sure that no duplicates can be inserted
    __table_args__ = (
        UniqueConstraint('home_team_name','away_team_name','match_slot','match_venue','match_date', name='unique_match'),
    )    
     
class Venue(db.Model):
    venue_id = db.Column(db.Integer, primary_key = True)
    venue_name = db.Column(db.String(150))
    
    venue_availability = db.Column(Boolean, default=True)
    accepts_outside_teams = db.Column(Boolean,default=True)
    
    slot_one = db.Column(Boolean,default = True)
    slot_two = db.Column(Boolean,default = True)
    slot_three = db.Column(Boolean,default = True)
    slot_four = db.Column(Boolean,default = True)
    slot_five = db.Column(Boolean,default = True)
    
    matches = db.relationship('AssignedMatch', backref = 'venue')
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
    __table_args__ = (
        UniqueConstraint('team_name','team_district_id','team_league_id', name='unique_team'),
    )    

class Admin(db.Model,UserMixin):
    admin_id = db.Column(db.Integer,primary_key = True)
    password = db.Column(db.String(150))
    user_name = db.Column(db.String(150))

