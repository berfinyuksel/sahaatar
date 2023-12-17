from flask import Blueprint,render_template,request,redirect,url_for,flash, current_app, session
from flask_bcrypt import Bcrypt
from datetime import datetime 
from sqlalchemy.exc import IntegrityError
from .models import District,League,Match,Team,Venue, AssignedMatch
import pandas as pd
import os
from . import db
from ast import literal_eval

views = Blueprint('views',__name__)

@views.before_request
def login_control():
    admin_pages = ['/venuesettings', '/addfile', '/fillform', '/optimize']

    if request.path in admin_pages and 'logged_in' not in session:
        return redirect(url_for('views.login'))

    # Check if the user is not logged in and trying to access other pages
    # if request.path != '/' and 'logged_in' not in session:
    #     return redirect(url_for('views.login'))

@views.route('/')
def home():
    file_path = 'website/static/excel/Matches.xlsx'

    df = pd.read_excel(file_path)

    # Sadece belirli sütunları seç
    selected_columns = ["time", "date","home_team", "away_team", "League_name", "venue_name"]
    df_selected = df[selected_columns]
    df_selected['date'] = pd.to_datetime(df_selected['date']).dt.strftime('%d/%m/%Y')
    df_selected = df_selected.sort_values(by='date', ascending=False)

    # Her sütunu ayrı ayrı HTML sayfalarına gönder
    time_html = df_selected['time'].to_frame().to_html(header=False,index=False)
    date_html = df_selected['date'].to_frame().to_html(header=False,index=False)
    home_team_html = df_selected['home_team'].to_frame().to_html(header=False,index=False)
    away_team_html = df_selected['away_team'].to_frame().to_html(header=False,index=False)
    league_name_html = df_selected['League_name'].to_frame().to_html(header=False,index=False)
    venue_name_html = df_selected['venue_name'].to_frame().to_html(header=False,index=False)
    return render_template('home_page.html',  
                           time=time_html,
                           date=date_html,
                           home=home_team_html,
                           away=away_team_html,
                           league=league_name_html,
                           venue=venue_name_html,
                           data=df_selected.to_html(header=False,index=False))

@views.route('/Login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        idInput = request.form.get('userID')
        passwordInput = request.form.get('password')
        if idInput == "berfin" and passwordInput == "123456":
            session['logged_in'] = True
            return redirect(url_for('views.home'))
        else:
            flash("Check your login information!")

    return render_template('login_page.html')

@views.route('/Logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('views.home'))

@views.route('/venuesettings',methods=['GET','POST'])
def venuesettings():
    venue = Venue.query.all()

    if request.method == "POST":
        selected_venue_name = request.form.get('venue', '')
        accept_input = request.form.get('area', 'False')
        open_input = request.form.get('open', 'False')

        if not selected_venue_name:
            flash("Venue is not selected. Please choose a venue.", "warning")
            return redirect(url_for("views.venuesettings"))

        slot_one_input = 'slot1' in request.form
        slot_two_input = 'slot2' in request.form
        slot_three_input = 'slot3' in request.form
        slot_four_input = 'slot4' in request.form
        slot_five_input = 'slot5' in request.form
        print(selected_venue_name)
        print(accept_input)
        print(open_input)
        if selected_venue_name and accept_input and open_input:
            venue_to_update = Venue.query.filter_by(venue_name = selected_venue_name).first()
            print(venue_to_update)
        
            venue_to_update.accepts_outside_teams = accept_input == 'True'
            venue_to_update.venue_availability = open_input == 'True'
            venue_to_update.slot_one = slot_one_input
            venue_to_update.slot_two = slot_two_input
            venue_to_update.slot_three = slot_three_input
            venue_to_update.slot_four = slot_four_input
            venue_to_update.slot_five = slot_five_input

            db.session.commit()
            flash("Changes saved Successfully!", "success")
        elif not selected_venue_name:
            flash("Select a Venue from the menu please!", "error")
        return redirect(url_for("views.venuesettings"))
    
    selected_venue = Venue.query.filter_by(venue_name = request.args.get('selected_venue')).first()
    return render_template('venuesettings.html', venue=venue, selected_venue = selected_venue)

@views.route('/venue_settings_selection', methods=['POST'])
def venue_settings_selection():
    #Select venue from form
    selected_venue_name = request.form['venue_name']
    return redirect(url_for('views.venuesettings', selected_venue=selected_venue_name))

@views.route('/addfile', methods=['POST', 'GET'])
def addfile():
    if request.method == 'POST':
                file = request.files['file']

                df = pd.read_excel(file, engine='openpyxl')
                try:
                    for index, row in df.iterrows():
                        home_team_to_insert = Team.query.filter_by(team_name=row["home_team"]).first()
                        away_team_to_insert = Team.query.filter_by(team_name=row["away_team"]).first()
                        league = League.query.filter_by(league_name=row['League_name']).first()

                        if home_team_to_insert and away_team_to_insert and league:
                            match = Match(
                                home_team_name=home_team_to_insert.team_name,
                                away_team_name=away_team_to_insert.team_name,
                                league_id=league.league_id,
                                match_day = row['Day'],
                                match_slot = row['Slots'],
                                match_date = row['Date']
                            )
                            try:
                                db.session.add(match)
                                db.session.commit()
            
                            except IntegrityError:
                                print(f"You have already added this match: {match}")
                                db.session.rollback()                

                    export_match_to_csv()
                    flash("Submitted Successfully!", "success")
                    return redirect(url_for("views.addfile"))
                except KeyError:
                    flash("Please enter the matches from the designated template!", "danger")
                    return redirect(url_for("views.addfile"))

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
        selected_date = request.form.get("trip-start")
        selected_slot = request.form.get("area")
        
        home_team = Team.query.filter_by(team_name=home_team_to_insert).first()
        away_team = Team.query.filter_by(team_name=away_team_to_insert).first()
        match_league_id = Team.query.filter_by(team_name=home_team_to_insert).first().team_league_id

        if home_team_to_insert == away_team_to_insert:
            flash("Home team and away team cannot be the same.", "danger")
            return redirect(url_for("views.fillform"))

        if check_match_condition(home_team, away_team):
            new_match = Match(
                home_team_name=home_team.team_name,
                away_team_name=away_team.team_name,
                league_id=match_league_id,
                match_date = datetime.strptime(selected_date, '%Y-%m-%d').date(),
                match_slot = selected_slot,
                match_day = datetime.strptime(selected_date,"%Y-%m-%d").strftime('%A').upper()

            )
            # 2023-12-21
            try:
                db.session.add(new_match)
                db.session.commit()
                flash("Submitted Successfully!", "success")
                return redirect(url_for("views.fillform"))
            except IntegrityError:
                db.session.rollback()
                flash("You have already added this match.", "danger")
                return redirect(url_for("views.fillform"))
    else:
        flash("Invalid request method", "danger")
        return redirect(url_for("views.fillform"))
    
    flash("Enter teams that are in the same league.", "danger")
    return redirect(url_for("views.fillform"))

@views.route('/fillform')
def fillform():
    team = Team.query.all()
    return render_template('fillform.html', team=team)

@views.route('/dashboard')
def dashboard():
    venue = Venue.query.all()
    return render_template('dashboard.html', venue=venue)

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

@views.route('/calendar', methods=['GET', 'POST'])
def calendar():
    venue = Venue.query.all()
    selected_venue_name = request.args.get('selected_venue') 
    print("**")

    mondayMatch = AssignedMatch.query.filter(AssignedMatch.match_venue == selected_venue_name).with_entities(AssignedMatch.home_team_name,AssignedMatch.away_team_name).all()

    for slot1 in mondayMatch:
        print(slot1)
        print("mac")

    print("----------------------------------------------------------------------------------")

    return render_template('calendar.html', venue=venue, selected_venue_name=selected_venue_name,mondayMatch=mondayMatch)
    
@views.route('/handle_venue_selection', methods=['POST'])
def handle_venue_selection():
    selected_venue_name = request.form['selected_venue']
    return redirect(url_for('views.calendar', selected_venue=selected_venue_name))

@views.route('/optimize', methods=['GET','POST'])
def optimize():
    league= League.query.all()
    league_name = request.form.get("league_name")
    return render_template('optimize.html', league=league)