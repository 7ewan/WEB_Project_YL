
import sqlite3
from data.songs import Song
from forms.song import SongForm
from forms.user import RegisterForm
from flask import Flask, render_template, request, make_response, session, flash, url_for
from flask_wtf import FlaskForm
from werkzeug.utils import redirect
from wtforms import StringField, PasswordField, SubmitField
from wtforms.fields.simple import EmailField, BooleanField, TextAreaField
from wtforms.validators import DataRequired
from data.users import User
from data import db_session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = '123'


@app.context_processor
def inject_user():
    from flask_login import current_user
    return dict(current_user=current_user)


login_manager = LoginManager()
login_manager.init_app(app)


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


def get_songs():
    con = sqlite3.connect('db/users.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT title, artist FROM songs")
    songs = cur.fetchall()
    con.close()
    return songs

@app.route('/')
def index():
    songs = get_songs()
    return render_template('index.html', title='Главная страница', songs=songs)




@app.route('/news')
def news():
    return render_template("news.html")


@app.route('/charts')
def charts():
    return render_template("charts.html")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/add_song', methods=['GET', 'POST'])
@login_required
def add_song():
    form = SongForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        song = Song(
            title=form.title.data,
            artist=form.artist.data,
            lyrics=form.lyrics.data,
            user_id=current_user.id
        )
        db_sess.add(song)
        db_sess.commit()
        flash('Песня добавлена!', 'success')
        return redirect('/')
    return render_template('add_song.html', title='Добавить песню', form=form)


@app.route('/song/<int:song_id>')
def song(song_id):
    db_sess = db_session.create_session()
    song = db_sess.query(Song).get(song_id)
    if not song:
        flash('Песня не найдена', 'danger')
        return redirect('/')
    return render_template('song.html', song=song)


@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return redirect('/')

    db_sess = db_session.create_session()
    songs = db_sess.query(Song).filter(
        (Song.title.ilike(f'%{query}%')) |
        (Song.artist.ilike(f'%{query}%'))
    ).all()

    return render_template('search_results.html', songs=songs, query=query)


if __name__ == '__main__':
    db_session.global_init('db/users.db')
    app.run(port=8080, host='127.0.0.1')