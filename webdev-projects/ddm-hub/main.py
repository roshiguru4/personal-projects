from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, Track, User
from flask_sqlalchemy import SQLAlchemy
from utils.yt_audio import download_youtube_audio
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash 
import os
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ddm.db"
app.config ["UPLOAD_FOLDER"] = "uploads"
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@app.route("/")
def root():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route("/index")
def index():
    tracks = Track.query.order_by(Track.id.desc()).all()
    return render_template("index.html", tracks=tracks)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        title = request.form["title"]
        team = request.form["team"]
        genre = request.form["genre"]
        year = int(request.form["year"])
        file_path = None
        filename = None
        youtube_url = request.form.get("youtube_url")
        file = request.files.get("audio")

        if file and file.filename.endswith(".mp3"):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
        
        elif youtube_url:
            filename = secure_filename(f"{title.replace(' ', '_')}.mp3")
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            try:
                download_youtube_audio(youtube_url, file_path)
            except Exception as e:
                return f"ERROR DOWNLOADIGN YOUTUBE AUDIO: {e}"
        
        else:
            return "PLEASE UPLOAD AN MP3 OR PROVIDE A YOUTUBE LINK."

        track = Track(
            title=title,
            file_path=filename,
            team=team,
            genre=genre,
            year=int(year)
        )
        db.session.add(track)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template("upload.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash('USERNAME ALREADY EXISTS.')
            return redirect(url_for("register"))
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by (username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash("INVALID CREDENTIALS.")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)


