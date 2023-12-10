from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from .models import Venue,District,Team,League,Match
from .extensions import db
from .data import districts,groups,teams_data,venue_data
from datetime import datetime, time

DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "Mama mia"
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .views import views

    app.register_blueprint(views,url_prefix = '/')

    create_database(app)
    insert_initial_data(app)
    

    return app

def create_database(app):
    if not path.exists('website/' + DB_NAME):
        with app.app_context():
            db.create_all()
        
        print("Created DB!")

def insert_initial_data(app):
    with app.app_context():
        districts_to_insert = districts
        groups_to_insert = groups
        teams_to_insert = teams_data
        venues_to_insert = venue_data

        for district_name in districts_to_insert:
            # Check if the district already exists
            existing_district = District.query.filter_by(district_name=district_name).first()

            if not existing_district:
                new_district = District(district_name=district_name)
                db.session.add(new_district)

        for group_name in groups_to_insert:
            # Check if the group already exists
            existing_group = League.query.filter_by(league_name=group_name).first()

            if not existing_group:
                new_group = League(league_name=group_name)
                db.session.add(new_group)

        for team in teams_to_insert:
            # Check if the team already exists
            existing_team = Team.query.filter_by(team_name=team["name"]).first()

            if not existing_team:
                # Find district and league by name
                district = District.query.filter_by(district_name=team["district"]).first()
                league = League.query.filter_by(league_name=team["group"]).first()

                if district and league:
                    new_team = Team(
                        team_name=team["name"],
                        team_district_id=district.district_id,
                        team_league_id=league.league_id
                    )
                    db.session.add(new_team)
                else:
                    print(f"Could not find district or league for team: {team['name']}")
        for venue in venues_to_insert:
            # Check if the venue already exists
            existing_venue = Venue.query.filter_by(venue_name=venue['venue_name']).first()
            

            if not existing_venue:
                # Find district by name
                district = District.query.filter_by(district_name=venue['district_name']).first()

                if district:
                    new_venue = Venue(
                        venue_name= venue['venue_name'],
                        venue_district_id= district.district_id,
                        venue_availability= venue['venue_availablity'],
                        accepts_outside_teams = venue['accepts_outside_teams'],
                        slot_one = venue['slot_one'],
                        slot_two = venue['slot_two'],
                        slot_three = venue['slot_three'],
                        slot_four = venue['slot_four'],
                        slot_five = venue['slot_five']
                    )
                    db.session.add(new_venue)
                else:
                    print(f"Could not find district or league for team: {venue['venue_name']}")       

        db.session.commit()

        print("Inserted initial data into the database!")
