from flask import Blueprint,render_template,request,redirect,url_for,flash,session
from datetime import datetime 
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func,distinct
from collections import defaultdict
from .models import League,Match,Team,Venue, AssignedMatch
import pandas as pd
import csv
from . import db
from datetime import datetime, timedelta
from .gurobi_test import run_gurobi

views = Blueprint('views',__name__)

@views.before_request
def login_control():
    admin_pages = ['/venuesettings', '/addfile', '/fillform', '/optimize']

    #kullanici giris yapmis mi kontrol et yapmamissa admin sayfalarinda logine yönlendir
    if request.path in admin_pages and 'logged_in' not in session:
        return redirect(url_for('views.login'))

@views.route('/')
def home():
    file_path = 'website/static/excel/Matches.xlsx'
    assigned_matches = AssignedMatch.query.all()
    matches = Match.query.all()
    
    if assigned_matches or matches:
        
        # Veritabanındaki maçları bir DataFrame'e dönüştürür
        # Veriyi ise AssignedMatches'te maçın olup olmadığına göre aktarır
        df_assigned = pd.DataFrame([
         {
            'time': match.match_slot,
            'date': match.match_date,
            'home_team': match.home_team_name,
            'away_team': match.away_team_name,
            'League_name': match.league_id,
            'venue_name': match.match_venue if match in assigned_matches else "" 
         }
         for match in assigned_matches or matches])
        

        #tarihi gün ay yil olarak goster
        df_assigned['date'] = pd.to_datetime(df_assigned['date']).dt.strftime('%d/%m/%Y')

        # Bulunduğumuz haftaya göre maçları filtrele
        df_assigned = current_week_filter(df_assigned)

        # DataFrame'i League_name ve tarihe göre sırala
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

            # Bulunduğumuz haftaya göre maçları filtrele
            df_selected = current_week_filter(df_selected)

            # DataFrame'i League_name ve tarihe göre sırala
            df_selected = df_selected.sort_values(by=['League_name', 'date'], ascending=[True, False])

            # Her sütunu ayrı ayrı HTML sayfalarına gönder
            return render_template(
                'home_page.html',
                time=df_selected['time'].to_frame().to_html(header=False, index=False),
                date=df_selected['date'].to_frame().to_html(header=False, index=False),
                home=df_selected['home_team'].to_frame().to_html(header=False, index=False),
                away=df_selected['away_team'].to_frame().to_html(header=False, index=False),
                league=df_selected['League_name'].to_frame().to_html(header=False, index=False),
                venue=df_selected['venue_name'].to_frame().to_html(header=False, index=False),
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
    #login attempt olunca id ve password dogruysa homepage'e gönder
    if request.method == 'POST':
        idInput = request.form.get('userID')
        passwordInput = request.form.get('password')
        if idInput == "berfin" and passwordInput == "123456":
            session['logged_in'] = True
            return redirect(url_for('views.home'))
        else:
            flash("Check your login information!")
    #login bilgileri dogru degilse login.htmlde kal ve flash mesaji göster
    return render_template('login_page.html')

@views.route('/Logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('views.home'))

@views.route('/venuesettings',methods=['GET','POST'])
def venuesettings():
    # Veritabanından tüm sahaları al
    venue = Venue.query.all()

    if request.method == "POST":
        # Form verilerini al
        selected_venue_name = request.form.get('venue', '')
        accept_input = request.form.get('area', 'False')
        open_input = request.form.get('open', 'False')
        
        # Bir sahanın seçilip seçilmediğini doğrula
        if not selected_venue_name:
            flash("Venue is not selected. Please choose a venue.", "warning")
            return redirect(url_for("views.venuesettings"))
        # Her bir zaman dilimi için slot bilgilerini al
        slot_one_input = 'slot1' in request.form
        slot_two_input = 'slot2' in request.form
        slot_three_input = 'slot3' in request.form
        slot_four_input = 'slot4' in request.form
        slot_five_input = 'slot5' in request.form
        
        if selected_venue_name and accept_input and open_input:
            venue_to_update = Venue.query.filter_by(venue_name = selected_venue_name).first()
        
            venue_to_update.accepts_outside_teams = accept_input == 'True'
            venue_to_update.venue_availability = open_input == 'True'
            venue_to_update.slot_one = slot_one_input
            venue_to_update.slot_two = slot_two_input
            venue_to_update.slot_three = slot_three_input
            venue_to_update.slot_four = slot_four_input
            venue_to_update.slot_five = slot_five_input
            
            # Değişiklikleri veritabanına kaydet
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
                # Kullanıcının seçtiği dosyayı alır
                file = request.files['file']

                df = pd.read_excel(file, engine='openpyxl')
                try:
                    # Veri çerçevesinde her bir satır için döngü oluştur
                    for index, row in df.iterrows():
                        # Satırdaki ev sahibi ve deplasman takımlarını sorgular
                        home_team_to_insert = Team.query.filter_by(team_name=row["home_team"]).first()
                        away_team_to_insert = Team.query.filter_by(team_name=row["away_team"]).first()
                        league = League.query.filter_by(league_name=row['League_name']).first()

                        if home_team_to_insert and away_team_to_insert and league:
                            # Yeni bir maç objesi oluştur
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
        # Formdan ev sahibi, deplasman, tarih ve slot bilgilerini al
        home_team_to_insert = request.form.get("home_team")
        away_team_to_insert = request.form.get("away_team")
        selected_date = request.form.get("start")
        selected_slot = request.form.get("area")
        # Ev sahibi ve deplasman takımlarını sorgula
        home_team = Team.query.filter_by(team_name=home_team_to_insert).first()
        away_team = Team.query.filter_by(team_name=away_team_to_insert).first()
        match_league_id = Team.query.filter_by(team_name=home_team_to_insert).first().team_league_id
        # Seçilen Ev sahibi ve deplasman takımları aynı mı diye kontrol et
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
                match_day = datetime.strptime(selected_date,"%Y-%m-%d").strftime('%A').upper() )
            
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

@views.route('/dashboard' , methods=['GET'])
def dashboard():
    #saha verilerini veritabanından alınması
    venue = Venue.query.all()

    #seçilen sahanın URL parametresinden alınması
    selected_venue = request.args.get('selected_venue', '')
    first_row = dashboard_firstrow(selected_venue)
    montly_game = dashboard_montly_game(selected_venue)
    league_chart= dashboard_league_chart(selected_venue)
    mostplayed_team=dashboard_mostplayed_team(selected_venue)
    lastmatch = dashboard_lastfive_match(selected_venue)
    #seçili sahanın altında yazan text
    venue_info = ""
    if selected_venue!='':
        venue_info = "The analysis report of the matches played on this field is given below."

    return render_template('dashboard.html', venue=venue,selected_venue=selected_venue, venue_info=venue_info, first_row=first_row,montly_game=montly_game,league_chart=league_chart,mostplayed_team=mostplayed_team,lastmatch=lastmatch)

#dropdown menuden saha seçiminin aktarımı
@views.route('/dashboard_venue_selection', methods=['POST'])
def dashboard_venue_selection():
    selected_venue_name = request.form['selected_venue']
    selectinfo = "The analysis report of the matches played on this field is given below."
    return redirect(url_for('views.dashboard', selected_venue=selected_venue_name))

@views.route('/calendar', methods=['GET', 'POST'])
def calendar():
    global current_week
    venue = Venue.query.all()
    selected_venue_name = request.args.get('selected_venue', '')  # URL parametresinden seçili mekan adını al

    weeklyMatchlist=getWeekMatches(selected_venue_name,current_week)    

    return render_template('calendar.html', venue=venue, selected_venue_name=selected_venue_name,weeklyMatchlist=weeklyMatchlist,current_week=current_week)

@views.route('/optimize', methods=['GET','POST'])
def optimize():
    league = League.query.all()

    if request.method == 'POST':
        export_match_to_csv()
        export_venue_to_csv()
        run_gurobi()
        extract_assigned_matches()
        

    return render_template('optimize.html', league=league)

#dashboarda yer alan ilk satırın bilgileri
def dashboard_firstrow(selected_venue):

    #güncel ayı atar
    current_month = datetime.now().month
    #bu haftayı istenilen formata çevirme
    start_date = datetime.strptime(current_week[0], '%d/%m/%Y').strftime('%Y-%m-%d')
    end_date = datetime.strptime(current_week[1], '%d/%m/%Y').strftime('%Y-%m-%d')

    #seçili sahada toplam oynanan maçların sorgusu
    total_game = AssignedMatch.query.filter(AssignedMatch.match_venue == selected_venue).count()

    #seçili sahada bu ay oynanan maç sayıları
    monthly_game = (AssignedMatch.query.filter
                    (AssignedMatch.match_venue == selected_venue,
                    func.extract('month', AssignedMatch.match_date) == current_month).count())
    
    #seçili sahada bu hafta oynanan maç sayıları
    weekly_game = AssignedMatch.query.filter(
                    AssignedMatch.match_venue == selected_venue, 
                    AssignedMatch.match_date.between(start_date, end_date)).count()
    
    #sahalarda toplam yapılan maçları çeker
    venue_ranked_list = (AssignedMatch.query
                         .with_entities(AssignedMatch.match_venue, func.count().label('venue_count'))
                         .group_by(AssignedMatch.match_venue).order_by(func.count().desc()).all())
    
    #sahaları en çok maç oynayanlara göre sıralar 
    ranked_num=1
    for venue in venue_ranked_list:
        if venue[0] == selected_venue:
            break
        else:
            ranked_num += 1
    #toplam maç sayıları, aylık maç sayıları , haftalık maçsayıları 
    #ve ranked_num içeren listeleri  first_row da birleştirme 
    first_row= [total_game,monthly_game,weekly_game,ranked_num]

    return first_row

def dashboard_montly_game(selected_venue):
    #seçili sahada oynanan maçları filtreleme ve aylara göre gruplama
    result = (
    AssignedMatch.query
    .filter(AssignedMatch.match_venue == selected_venue)
    .with_entities(
        distinct(func.strftime('%m', AssignedMatch.match_date)).label('ay'),
        func.count().label('mac_sayisi')
    )
    .group_by(func.strftime('%Y-%m', AssignedMatch.match_date))
    .order_by(func.strftime('%Y-%m', AssignedMatch.match_date)).all()
    )
    #result listesindeki ayları ve maç sayılarını ayrı listelere ayırma
    aylar = [datetime.strptime(ay, '%m').strftime('%B') for ay, _ in result]
    mac_sayisi = [mac_sayisi for _, mac_sayisi in result]
    
    #aylar ve maç sayılarını içeren listeleri birleştirme
    second_row = [aylar,mac_sayisi]
    return second_row
    
def dashboard_league_chart(selected_venue):

    #seçili sahada yapılan maçları liglere göre gruplandırma ve maç sayısını hesaplama
    result = (
    AssignedMatch.query
    .filter(AssignedMatch.match_venue == selected_venue)
    .group_by(AssignedMatch.league_id)
    .with_entities(AssignedMatch.league_id, func.count().label('satir_sayisi'))
    .all()
    )
    #liglere göre maç sayılarını içeren bir liste oluşturma
    lig_mac_sayisi=[]
    for lig in result:
        lig_mac_sayisi.append(lig[1])

    return lig_mac_sayisi

def dashboard_mostplayed_team(selected_venue):
    # ev sahibi olan takımların seçili sahada yapılan maç sayılarını bulma
    home_team_result = (
    AssignedMatch.query
    .with_entities(AssignedMatch.home_team_name.label('takim'), func.count().label('mac_sayisi'))
    .filter(AssignedMatch.match_venue == selected_venue)
    .group_by('takim')
    .order_by(func.count().desc())
    .all()
    )
     #deplasman takımlarının seçili sahada yapılan maç sayılarını bulma
    away_team_result = (
    AssignedMatch.query
    .with_entities(AssignedMatch.away_team_name.label('takim'), func.count().label('mac_sayisi'))
    .filter(AssignedMatch.match_venue == selected_venue)
    .group_by('takim')
    .order_by(func.count().desc())
    .all()
    )
    #maç sayılarını defaultdict fonksiyonu ile  takım bazında toplanması
    combined_result = defaultdict(int)
    for row in home_team_result:
        takim = row.takim
        mac_sayisi = row.mac_sayisi
        combined_result[takim] += mac_sayisi
    for row in away_team_result:
        takim = row.takim
        mac_sayisi = row.mac_sayisi
        combined_result[takim] += mac_sayisi
    #toplam maç sayılarına göre takımları sıralama    
    sorted_result = sorted(combined_result.items(), key=lambda x: x[1], reverse=True)

    # İlk 5 takımı ve maç sayılarını ayrı listelere ayırma
    top_5_teams = [team[0] for team in sorted_result[:5]]
    top_5_values = [team[1] for team in sorted_result[:5]]

    fourth_row=[top_5_teams,top_5_values]
    return fourth_row

def dashboard_lastfive_match(selected_venue):
    # Match günlerini istenilen formata çevirme
    today = datetime.now().strftime('%Y-%m-%d')

    # Query ile seçili gündeki maçları çekme
    lastmatch = AssignedMatch.query.filter(
        AssignedMatch.match_venue == selected_venue,
        AssignedMatch.match_date <= today).with_entities(
        AssignedMatch.home_team_name,
        AssignedMatch.away_team_name,
        AssignedMatch.match_date
    ).order_by(AssignedMatch.match_date.desc(),AssignedMatch.match_slot.desc()).limit(5)

    # Her bir row'daki attributeleri string olarak birleştirme
    result_strings = []
    for match in lastmatch:
        match_string = f"{match[0]} vs {match[1]} "
        date_string = f"{match[2]}"
        result_strings.append(date_string)
        result_strings.append(match_string)

    return result_strings

# İki takımın aynı ligde olup olmadığını karşılaştırıyor
def check_match_condition(team_one: Team, team_two: Team):
    return team_one.team_league_id == team_two.team_league_id

# Csv dosyasını açıp içindeki verileri aktarmak için bir fonksiyon
def load_csv(file_path):
    with open(file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        csv_data = list(csv_reader)
    return csv_data
# Csv dosyalarına ekstra column ekler
def add_column(csv_data, default_value):
    for row in csv_data:
        row.append(default_value)
    return csv_data
# Csv dosyası yazdırır
def save_csv(csv_data, file_path):
    with open(file_path, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerows(csv_data)    

# Maç verilerini Csv'e aktarır
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

    # Convert each row to a list of values
    rows_as_lists = matches_df.values.tolist()
    
    # Write each row to the CSV file line by line
    save_csv(rows_as_lists,'website/gurobi input/matches.csv')

# Saha verilerini Csv'e aktarır
def export_venue_to_csv():
    venues = Venue.query.all()

    # Venue name , Venue availability, slot1 , slot2,slot3,slot4,slot5
    venues_df = pd.DataFrame(
        {
            "venue_id": [venue.venue_id for venue in venues],
            "venue_name": [venue.venue_name for venue in venues],
            "venue_availability": [venue.venue_availability for venue in venues],
            "slot_one": [venue.slot_one for venue in venues],
            "slot_two": [venue.slot_two for venue in venues],
            "slot_three": [venue.slot_three for venue in venues],
            "slot_four": [venue.slot_four for venue in venues],
            "slot_five": [venue.slot_five for venue in venues],
        }
    )

    # Convert each row to a list of values
    rows_as_lists = venues_df.values.tolist()

    # Write each row to the CSV file line by line
    save_csv(rows_as_lists,'website/gurobi input/venues.csv')

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
            if slot[2] == "SLOT1":
                day[0] = slot[0] + " - " + slot[1]
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

# AssignedMatches.csv dosyasından atanmış maçları veritabanına aktarır
def extract_assigned_matches():
        match_data = load_csv('website/gurobi input/matches.csv')

        # Gurobi kodu olmadığı için yeni column olarak "Not Assigned" ekler
        modified_data = add_column(match_data, 'Not Assigned')

        # Eklenilmiş veriyi yeni bir csv olarak yazdırır
        save_csv(modified_data, 'website/gurobi output/AssignedMatches.csv')

        match_data = load_csv('website/gurobi output/AssignedMatches.csv')

        for row in match_data[0:]:
                match = AssignedMatch(
                        home_team_name = row[1],
                        away_team_name = row[2],
                        league_id = row[3],
                        match_day = row[4],
                        match_slot = row[5],
                        match_date = datetime.strptime(row[6].strip(), '%d/%m/%Y').date()
                    )
                try:
                        db.session.add(match)
                        db.session.commit()
                except IntegrityError:
                        print(f"You have already added this match: {match}")
                        db.session.rollback()        

        db.session.commit()
        delete_all_matches()
        flash("Assigned Successfully!", "success")

def delete_all_matches():
    try:
        # Veritabanındaki maçları siler
        db.session.query(Match).delete()

        # Değişiklikleri veritabanına aktarır
        db.session.commit()
        print("All data deleted from Matches table.")
    except Exception as e:
        # Exception atarsa geç
        db.session.rollback()
        print(f"Error deleting data: {str(e)}")
    finally:
        db.session.close()
        
def current_week_filter(df):
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    start_of_week = pd.to_datetime(start_of_week)
    end_of_week = pd.to_datetime(end_of_week)
    df = df[
            (pd.to_datetime(df['date']) >= start_of_week) &
            (pd.to_datetime(df['date']) <= end_of_week)
        ]
    return df        