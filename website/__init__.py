from flask import Flask
import pandas as pd
from os import path
from .models import Venue,District,Team,League,AssignedMatch
from .extensions import db
from .data import districts,groups,venue_data
from sqlalchemy.exc import IntegrityError

DB_NAME = "database.db"

# Burada uygulamayı çalıştırmak ve ayarlamalarını yapmak için fonksiyon yazıyoruz
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "Mama mia"
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    # Veritabanını uygulama çağrılırken aynı bağlamda çalıştırmak için init_app() fonksiyonunu çağırıyoruz
    db.init_app(app)

    from .views import views
    # Burada ise uygulama çağrılırken front-end kısmı ile iletişime geçtiğimiz views objesini bağlıyoruz
    app.register_blueprint(views,url_prefix = '/')

    create_database(app)
    insert_initial_data(app)
    

    return app
# Veritabanını oluşturmak için ayrı bir fonksiyon
def create_database(app):
    if not path.exists('website/' + DB_NAME):
        with app.app_context():
            db.create_all()
        
        print("Created DB!")
# Veritabanına ilk verileri eklemek için ayrı bir fonksiyon
def insert_initial_data(app):  
    with app.app_context():
        if not (District.query.all() and League.query.all() and Venue.query.all()):
           districts_to_insert = districts
           groups_to_insert = groups
           venues_to_insert = venue_data

           for district in districts_to_insert:
               try:
                   db.session.add(District(district_name = district))
               except IntegrityError:
                   db.session.rollback()

           for group in groups_to_insert:
               try:
                   db.session.add(League(league_name = group))
               except IntegrityError:
                   db.session.rollback()

           team_path = 'website/static/excel/Teams.xlsx'
           df_team = pd.read_excel(team_path)
           for index, row in df_team.iterrows():
               try:
                   team_to_insert = row["team_name"]
                   league = League.query.filter_by(league_name=row['League_name']).first()
                   team_location = District.query.filter_by(district_name=row['team_location']).first()

                   if team_to_insert and team_location and league:
                       team = Team(
                           team_name = team_to_insert,
                           team_league_id = league.league_id,
                           team_district_id = team_location.district_id
                       )
                       try:
                           db.session.add(team)
                           db.session.commit()
                       except IntegrityError as e:
                           db.session.rollback()            
               except KeyError as e:
                   print(f"KeyError in row {index}: {e}")
                   print("Please enter the right template!")

           for venue in venues_to_insert:
               # Veritabanında böyle bir sahanın olup olmadığını kontrol eder 
               existing_venue = Venue.query.filter_by(venue_name=venue['venue_name']).first()
               
               if not existing_venue:
                   # Sahanın ismini veritabında sorguluyor
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

           match_path = 'website/static/excel/AssignedMatches.xlsx'
           df_match = pd.read_excel(match_path)
           for index, row in df_match.iterrows():
               try:
                   home_team_to_insert = Team.query.filter_by(team_name=row["home_team"]).first()
                   away_team_to_insert = Team.query.filter_by(team_name=row["away_team"]).first()
                   league = League.query.filter_by(league_name=row['League_name']).first()
                   venue = Venue.query.filter_by(venue_name=row['Venue']).first()

                   if home_team_to_insert and away_team_to_insert and league and venue:
                       match = AssignedMatch(
                           home_team_name = home_team_to_insert.team_name,
                           away_team_name = away_team_to_insert.team_name,
                           league_id = league.league_id,
                           match_venue = venue.venue_name,
                           match_day = row['Day'],
                           match_slot = row['Slots'],
                           match_date = row['Date'],
                           match_week = row['Week']
                       )

                       try:
                           db.session.add(match)
                           db.session.commit()
                       except IntegrityError:
                           db.session.rollback()

               except KeyError as e:
                   print(f"KeyError in row {index}: {e}")
                   print("Please enter the right template!")                  

           db.session.commit()

           print("Inserted initial data into the database!")      