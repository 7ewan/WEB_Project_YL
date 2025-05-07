from flask import Flask, render_template, request, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.fields.simple import EmailField, BooleanField
from wtforms.validators import DataRequired
from data.songs import Song, Annotation
from data.users import User
from data import db_session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = '123'

login_manager = LoginManager()
login_manager.init_app(app)


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    about = TextAreaField('О себе')
    submit = SubmitField('Зарегистрироваться')


class SongForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    artist = StringField('Исполнитель', validators=[DataRequired()])
    lyrics = TextAreaField('Текст песни', validators=[DataRequired()])
    submit = SubmitField('Добавить')


def censor_vowel_words(text):
    if not text:
        return text
    vowel_pattern = r'(^|\s)([ауоиэыяюеёАУОИЭЫЯЮЕЁaeiouyAEIOUY]\w*)'
    return re.sub(vowel_pattern, r'\1#$@%', text, flags=re.IGNORECASE | re.UNICODE)


def get_recent_songs(limit=6):
    db_sess = db_session.create_session()
    songs = db_sess.query(Song).order_by(Song.created_date.desc()).limit(limit).all()
    db_sess.close()
    return songs


@app.route('/')
def index():
    songs = get_recent_songs()
    return render_template('index.html', title='Главная страница', songs=songs)


@app.route('/news')
def news():
    return render_template("news.html")


@app.route('/charts')
def charts():
    db_sess = db_session.create_session()
    top_songs = db_sess.query(Song).order_by(Song.views.desc()).limit(10).all()
    db_sess.close()
    return render_template('charts.html', title='Чарты', top_songs=top_songs)


@app.route('/song/<int:song_id>')
def song(song_id):
    db_sess = db_session.create_session()
    song = db_sess.query(Song).get(song_id)
    if not song:
        flash('Песня не найдена', 'danger')
        return redirect('/')

    song.views = song.views + 1 if song.views else 1
    db_sess.commit()

    return render_template('song.html', song=song)

@app.route('/add_views_field')
def add_views_field():
    db_sess = db_session.create_session()
    songs = db_sess.query(Song).all()
    for song in songs:
        if song.views is None:
            song.views = 0
    db_sess.commit()
    return "Поле views добавлено ко всем песням"

@app.route('/song/<int:song_id>/add_annotation', methods=['GET', 'POST'])
@login_required
def add_annotation(song_id):
    if request.method == 'POST':
        db_sess = db_session.create_session()
        annotation = Annotation(
            text=request.form['annotation_text'],
            user_id=current_user.id,
            song_id=song_id,
            created_at=datetime.utcnow()
        )
        db_sess.add(annotation)
        db_sess.commit()
        flash('Аннотация добавлена!', 'success')
        return redirect(url_for('song', song_id=song_id))
    return redirect(url_for('song', song_id=song_id))


@app.route('/add_song', methods=['GET', 'POST'])
@login_required
def add_song():
    form = SongForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        song = Song(
            title=form.title.data,
            artist=form.artist.data,
            lyrics=censor_vowel_words(form.lyrics.data),
            user_id=current_user.id,
            created_date=datetime.utcnow()
        )
        db_sess.add(song)
        db_sess.commit()
        flash('Песня добавлена!', 'success')
        return redirect('/')
    return render_template('add_song.html', title='Добавить песню', form=form)


@app.route('/all_songs')
def all_songs():
    db_sess = db_session.create_session()
    songs = db_sess.query(Song).order_by(Song.created_date.desc()).all()
    db_sess.close()
    return render_template('all_songs.html', title='Все песни', songs=songs)


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
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form, message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form, message="Такой пользователь уже есть")
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


if __name__ == '__main__':
    db_session.global_init('db/users.db')
    app.run(port=8080, host='127.0.0.1', debug=True)
