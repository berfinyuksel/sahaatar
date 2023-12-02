from flask import Blueprint,render_template,request,redirect,url_for,flash
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError
from .models import District,League,Match,Team
import pandas as pd
from . import db

views = Blueprint('views',__name__)

@views.route('/')
def home():
    return render_template('home_page.html')

@views.route('/Login', methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        idInput = request.form.get('userID')
        passwordInput = request.form.get('password')
        if idInput == "berfin" and passwordInput == "123456":
            return redirect(url_for('views.adminhome'))
        else: 
            flash("Check your login information!")

    return render_template('login_page.html')

@views.route('/adminhome')
def adminhome():
    return render_template('admin_home_page.html')

@views.route('/fieldsettings')
def fieldsettings():
    return render_template('fieldsettings.html')


@views.route('/addfile', methods=['POST', 'GET'])
def addfile():
    if request.method == 'POST':
                file = request.files['file']

                df = pd.read_excel(file, engine='openpyxl')

                for index, row in df.iterrows():
                    home_team_to_insert = Team.query.filter_by(team_name=row["home_team"]).first()
                    away_team_to_insert = Team.query.filter_by(team_name=row["away_team"]).first()
                    league = League.query.filter_by(league_name=row['League_name']).first()

                    if home_team_to_insert and away_team_to_insert and league:
                        match = Match(
                            home_team_name=home_team_to_insert.team_name,
                            away_team_name=away_team_to_insert.team_name,
                            league_id=league.league_id
                        )
                        try:
                            db.session.add(match)
                            db.session.commit()
                        except IntegrityError:
                            print(f"You have already added this match: {match}")
                            db.session.rollback()

                db.session.commit()

    export_match_to_csv()

    return render_template('addfile.html')

@views.route('/deletefile', methods=['DELETE'])
def delete_file():
    try:
        file_name = request.json.get('fileName')
        return '', 204  # No content, success
    except Exception as e:
        print(f'Error deleting file: {e}')
        return '', 500  # Internal Server Error

@views.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        print(request.form)
        home_team_to_insert = request.form.get("home_team")
        away_team_to_insert = request.form.get("away_team")
        
        home_team = Team.query.filter_by(team_name = home_team_to_insert).first()
        away_team = Team.query.filter_by(team_name = away_team_to_insert).first()
        match_league_id = Team.query.filter_by(team_name=home_team_to_insert).first().team_league_id

        if check_match_condition(home_team,away_team):
            new_match = Match(home_team_name=home_team.team_name, 
                              away_team_name=away_team.team_name,
                              league_id = match_league_id)
            try:
                    db.session.add(new_match)
                    db.session.commit()
            except IntegrityError:
                    print(f"You have already added this match: {new_match}")
                    db.session.rollback()
           

            return f"Selected Home Team: {home_team.team_name}, Selected Away Team: {away_team.team_name}"
    else:
        return "Invalid request method"

@views.route('/fillform')
def fillform():
    team = Team.query.all()
    return render_template('fillform.html', team=team)

@views.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# İki takımın aynı ligde olup olmadığını karşılaştırıyor
def check_match_condition(team_one: Team, team_two: Team):
    return team_one.team_league_id == team_two.team_league_id

def export_match_to_csv():
    # Match tablosundaki verileri çek
    matches = Match.query.all()

    # Match verilerini bir veri çerçevesine dönüştür
    matches_df = pd.DataFrame([match.home_team_name for match in matches])

    # Veri çerçevesini CSV dosyasına kaydet
    matches_df.to_csv('matches.csv', index=False)

    print("Match data saved to CSV file successfully.")
