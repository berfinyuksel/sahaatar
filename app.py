from flask import flash
from flask import Flask, redirect, render_template, request, url_for
from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash,check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

@app.route('/')
def home():
    return render_template('home_page.html')

@app.route('/Login', methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        idInput = request.form.get('userID')
        passwordInput = request.form.get('password')
        if idInput == "A" and passwordInput == "B":
            return redirect(url_for('adminhome'))
        # else:
        #     flash('Your userID or password is incorrect. For login issues contact with +90 XXX XXX XX XX', 'danger')

    return render_template('login_page.html')

@app.route('/adminhome')
def adminhome():
    return render_template('admin_home_page.html')

if __name__ == "__main__":
    app.run(debug=True)