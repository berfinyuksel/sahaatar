from flask import Blueprint,render_template,request,redirect,url_for,flash, current_app, session
from flask_bcrypt import Bcrypt
from datetime import datetime 
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from .models import District,League,Match,Team,Venue, AssignedMatch
import pandas as pd
import os
from . import db
from ast import literal_eval
from datetime import datetime, timedelta
from .gurobi_test import run_gurobi

views = Blueprint('views',__name__)

@views.before_request
def login_control():
    admin_pages = ['/venuesettings', '/addfile', '/fillform', '/optimize']

    if request.path in admin_pages and 'logged_in' not in session:
        return redirect(url_for('views.login'))

@views.route('/')
def home():
    file_path = 'website/static/excel/Matches.xlsx'
    assigned_matches = AssignedMatch.query.all()
    
    if assigned_matches:
        df_assigned = pd.DataFrame([
            {
                'time': match.match_slot,
                'date': match.match_date,
                'home_team': match.home_team_name,
                'away_team': match.away_team_name,
                'League_name': match.league_id,
                'venue_name': match.match_venue
            }
            for match in assigned_matches
        ])

        # Format the 'date' column
        df_assigned['date'] = pd.to_datetime(df_assigned['date']).dt.strftime('%d/%m/%Y')

        # Filter matches for the current week
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        start_of_week = pd.to_datetime(start_of_week)
        end_of_week = pd.to_datetime(end_of_week)
        df_assigned = df_assigned[
            (pd.to_datetime(df_assigned['date']) >= start_of_week) &
            (pd.to_datetime(df_assigned['date']) <= end_of_week)
        ]

        # Sort the DataFrame first by 'League_name' and then by 'date'
        df_assigned = df_assigned.sort_values(by=['League_name', 'date'], ascending=[True, False])

        return render_template(
            'home_page.html',
            time=df_assigned['time'].to_frame().to_html(header=False, index=False),
            date=df_assigned['date'].to_frame().to_html(header=False, index=False),
            home=df_assigned['home_team'].to_frame().to_html(header=False, index=False),
            away=df_assigned['away_team'].to_frame().to_html(header=False, index=False),
            league=df_assigned['League_name'].to_frame().to_html(header=False, index=False),
            venue=df_assigned['venue_name'].to_frame().to_html(header=False, index=False),
            data=df_assigned.to_html(header=False, index=False)
        )
    else:
        try:
            df = pd.read_excel(file_path)
            # Sadece belirli sütunları seç
            selected_columns = ["time", "date", "home_team", "away_team", "League_name", "venue_name"]
            df_selected = df[selected_columns]
            df_selected['date'] = pd.to_datetime(df_selected['date']).dt.strftime('%d/%m/%Y')

            # Filter matches for the current week
            today = datetime.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            start_of_week = pd.to_datetime(start_of_week)
            end_of_week = pd.to_datetime(end_of_week)
            df_selected = df_selected[
                (pd.to_datetime(df_selected['date']) >= start_of_week) &
                (pd.to_datetime(df_selected['date']) <= end_of_week)
            ]

            # Sort the DataFrame first by 'League_name' and then by 'date'
            df_selected = df_selected.sort_values(by=['League_name', 'date'], ascending=[True, False])

            # Her sütunu ayrı ayrı HTML sayfalarına gönder
            time_html = df_selected['time'].to_frame().to_html(header=False, index=False)
            date_html = df_selected['date'].to_frame().to_html(header=False, index=False)
            home_team_html = df_selected['home_team'].to_frame().to_html(header=False, index=False)
            away_team_html = df_selected['away_team'].to_frame().to_html(header=False, index=False)
            league_name_html = df_selected['League_name'].to_frame().to_html(header=False, index=False)
            venue_name_html = df_selected['venue_name'].to_frame().to_html(header=False, index=False)

            return render_template(
                'home_page.html',
                time=time_html,
                date=date_html,
                home=home_team_html,
                away=away_team_html,
                league=league_name_html,
                venue=venue_name_html,
                data=df_selected.to_html(header=False, index=False)
            )
        except FileNotFoundError:
            return render_template(
                'home_page.html',
                time="Empty",
                date="Empty",
                home="Empty",
                away="Empty",
                league="Empty",
                venue="Empty",
                data="Empty"
            )

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

#dashboarda yer alan ilk satırın bilgileri
def dashboard_firstrow(selected_venue):

    #güncel ayı atar
    current_month = datetime.now().month

    #toplam oynanan maçların sorgusu
    total_game = AssignedMatch.query.filter(AssignedMatch.match_venue == selected_venue).count()

    #bu haftayı istenilen formata çevirme
    start_date = datetime.strptime(current_week[0], '%d/%m/%Y').strftime('%Y-%m-%d')
    end_date = datetime.strptime(current_week[1], '%d/%m/%Y').strftime('%Y-%m-%d')

    #bu ay oynanan maç sayıları
    monthly_game = AssignedMatch.query.filter(AssignedMatch.match_venue == selected_venue,func.extract('month', AssignedMatch.match_date) == current_month).count()

    #bu hafta oynanan maç sayıları
    weekly_game = AssignedMatch.query.filter(AssignedMatch.match_venue == selected_venue, AssignedMatch.match_date.between(start_date, end_date)).count()

    #sahalarda toplam yapılan maçları çeker
    venue_ranked_list = (
    AssignedMatch.query
    .with_entities(AssignedMatch.match_venue, func.count().label('venue_count'))
    .group_by(AssignedMatch.match_venue)
    .order_by(func.count().desc())
    .all()
        )
    
    #sahaların en çok maç oynayanlara göre sıralar
    ranked_num=1
    for venue in venue_ranked_list:

        if venue[0] == selected_venue:
            break
        else:
            ranked_num += 1

    first_row= [total_game,monthly_game,weekly_game,ranked_num]

    return first_row

@views.route('/dashboard' , methods=['GET'])
def dashboard():
    #saha verilerini veritabanından alınması
    venue = Venue.query.all()

    #seçilen sahanın URL parametresinden alınması
    selected_venue = request.args.get('selected_venue', '')
    first_row = dashboard_firstrow(selected_venue)
    #seçili sahanın altında yazan text
    venue_info = ""
    if selected_venue!='':
        venue_info = selected_venue + "'nda oynanan maçlarının analiz raporu aşağıda yer almaktadır."

    return render_template('dashboard.html', venue=venue,selected_venue=selected_venue, venue_info=venue_info, first_row=first_row)

#dropdown menuden saha seçiminin aktarımı
@views.route('/dashboard_venue_selection', methods=['POST'])
def dashboard_venue_selection():
    selected_venue_name = request.form['selected_venue']
    selectinfo = selected_venue_name + " nda oynanan maçlarının analiz raporu aşağıda yer almaktadır."
    return redirect(url_for('views.dashboard', selected_venue=selected_venue_name))


# İki takımın aynı ligde olup olmadığını karşılaştırıyor
def check_match_condition(team_one: Team, team_two: Team):
    return team_one.team_league_id == team_two.team_league_id

def export_match_to_csv():
    # Match tablosundaki verileri çek
    matches = Match.query.all()

    # Match verilerini bir veri çerçevesine dönüştür
    matches_df = pd.DataFrame({
        'match_id': [match.match_id for match in matches],
        'home_team': [match.home_team_name for match in matches],
        'away_team': [match.away_team_name for match in matches],
        'League_name': [match.league_id for match in matches],
        'Day': [match.match_day for match in matches],
        'Slots': [match.match_slot for match in matches],
        'Date': [str(match.match_date.strftime("%d/%m/%Y")) for match in matches]
    })
    match_list= []
    # Convert each row to a list of values
    rows_as_lists = matches_df.values.tolist()
    for rows in rows_as_lists:
        match_list.append(rows)

    # Write each row to the CSV file with double square brackets
    with open('matches.csv', 'w') as csv_file:
        csv_file.write(str(match_list))

def export_venue_to_csv():
    venues = Venue.query.all()

    #Venue name , Venue availability, slot1 , slot2,slot3,slot4,slot5
    venues_df = pd.DataFrame (
        {
            "venue_id" : [venue.venue_id for venue in venues],
            "venue_name" : [venue.venue_name for venue in venues],
            "venue_availability" : [venue.venue_availability for venue in venues],
            "slot_one" : [venue.slot_one for venue in venues],
            "slot_two" : [venue.slot_two for venue in venues],
            "slot_three" : [venue.slot_three for venue in venues],
            "slot_four" : [venue.slot_four for venue in venues],
            "slot_five" : [venue.slot_five for venue in venues],
        }
    )
    rows_as_lists = venues_df.values.tolist()
    venue_list = []

    for rows in rows_as_lists:
        venue_list.append(rows)

    with open('venues.csv', 'w') as csv_file:
        csv_file.write(str(venue_list))
   
@views.route('/calendar', methods=['GET', 'POST'])
def calendar():
    global current_week
    venue = Venue.query.all()
    selected_venue_name = request.args.get('selected_venue', '')  # URL parametresinden seçili mekan adını al

    weeklyMatchlist=getWeekMatches(selected_venue_name,current_week)    

    return render_template('calendar.html', venue=venue, selected_venue_name=selected_venue_name,weeklyMatchlist=weeklyMatchlist,current_week=current_week)

#tarih aralığını alma
def getWeekRangeString(date):
    start_of_week = date - timedelta(days=date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    current_week=[start_of_week.strftime("%d/%m/%Y") , end_of_week.strftime("%d/%m/%Y")]
    return current_week
#seçili haftanın maç takviminin oluşturulması
def getWeekMatches(selected_venue_name, current_week):
    monday = ["-", "-", "-", "-", "-"]
    tuesday = ["-", "-", "-", "-", "-"]
    wednesday = ["-", "-", "-", "-", "-"]
    thursday = ["-", "-", "-", "-", "-"]
    friday = ["-", "-", "-", "-", "-"]
    saturday = ["-", "-", "-", "-", "-"]
    sunday = ["-", "-", "-", "-", "-"]

    week = [monday, tuesday, wednesday, thursday, friday, saturday, sunday]
    gunler = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY","SUNDAY"]

    gun=0

    for day in week:
        fake_day=getDayMatches(selected_venue_name,current_week,gun)
        gun +=1
        for slot in fake_day:
            print(slot[2])
            if slot[2] == "SLOT1":
                day[0] = slot[0] + " - " + slot[1]
                print(day[0])
            elif slot[2] == "SLOT2":
                day[1] = slot[0] + " - " + slot[1]
            elif slot[2] == "SLOT3":
                day[2] = slot[0] + " - " + slot[1]
            elif slot[2] == "SLOT4":
                day[3] = slot[0] + " - " + slot[1]
            elif slot[2] == "SLOT5":
                day[4] = slot[0] + " - " + slot[1]

    return week
#seçili günün maç takviminin oluşturulması
def getDayMatches(selected_venue_name, current_week,gun):
    gunler = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY","SUNDAY"]

    #match günlerini istenilen formata çevirme
    start_date = datetime.strptime(current_week[0], '%d/%m/%Y').strftime('%Y-%m-%d')
    end_date = datetime.strptime(current_week[1], '%d/%m/%Y').strftime('%Y-%m-%d')

    #query ile seçili gündeki maçları çekme
    daymatch = AssignedMatch.query.filter(AssignedMatch.match_venue == selected_venue_name, AssignedMatch.match_day==gunler[gun],    
    AssignedMatch.match_date.between(start_date, end_date)).with_entities(AssignedMatch.home_team_name,
    AssignedMatch.away_team_name,AssignedMatch.match_slot).order_by(AssignedMatch.match_slot).all()
    
    return daymatch

#önceki hafta geçme
@views.route('/prev_week', methods=['GET'])
def prev_week():
    global current_week
    current_week[0] = (datetime.strptime(current_week[0], "%d/%m/%Y") - timedelta(days=7)).strftime("%d/%m/%Y")
    current_week[1] = (datetime.strptime(current_week[1], "%d/%m/%Y") - timedelta(days=7)).strftime("%d/%m/%Y")
    return redirect(url_for('views.calendar', selected_venue=request.args.get('selected_venue'), current_week=current_week))

#sonraki hafya geçme
@views.route('/next_week', methods=['GET'])
def next_week():
    global current_week
    current_week[0] = (datetime.strptime(current_week[0], "%d/%m/%Y") + timedelta(days=7)).strftime("%d/%m/%Y")
    current_week[1] = (datetime.strptime(current_week[1], "%d/%m/%Y") + timedelta(days=7)).strftime("%d/%m/%Y")
    return redirect(url_for('views.calendar', selected_venue=request.args.get('selected_venue'), current_week=current_week))

current_week = getWeekRangeString(datetime.now())

@views.route('/handle_venue_selection', methods=['POST'])
def handle_venue_selection():
    # formdan seçili mekanı alma
    selected_venue_name = request.form['selected_venue']
    global current_week
    current_week = getWeekRangeString(datetime.now())
    return redirect(url_for('views.calendar', selected_venue=selected_venue_name, current_week=current_week))

@views.route('/optimize', methods=['GET','POST'])
def optimize():
    league= League.query.all()
    league_name = request.form.get("league_name")
    if request.method == 'POST':
        export_match_to_csv()
        export_venue_to_csv()
        run_gurobi()
    return render_template('optimize.html', league=league)