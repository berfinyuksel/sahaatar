from flask import Blueprint,render_template,request,redirect,url_for,flash
from flask_bcrypt import Bcrypt
from .models import Admin
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

@views.route('/addfile')
def addfile():
    return render_template('sendfile.html')

@views.route('/fillform')
def fillform():
    return render_template('fillform.html')
