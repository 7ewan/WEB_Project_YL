from flask import Flask, render_template, request, flash, redirect, url_for
from data.songs import Song, Annotation
from data.users import User
from forms.user import LoginForm, RegisterForm
from forms.song import SongForm
from data import db_session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
import re
from flask_restful import Api
from web_song_api import SongListResource, SongResource
from song_api import SongFullSearchResource
import yandex_music
import random
from sqlalchemy import func
from seed_data import seed_test_data


app = Flask(__name__)
app.config['SECRET_KEY'] = '123'

login_manager = LoginManager()
login_manager.init_app(app)
api = Api(app)


def find_yandex_track(title, artist):
    client = yandex_music.Client().init()
    search_text = f"{artist} {title}"
    search_result = client.search(search_text)

    if search_result.best and search_result.best.type == 'track':
        track = search_result.best.result
        return track.id, track.albums[0].id
    return None, None


def censor_vowel_words(text):
    if not text:
        return text
    replacement_words = ['СВАГА', 'ДРИПЧИК', 'МАЙОНЕЗ', 'КАРТЕЛЬ', 'ЧУВАААААК']
    vowel_pattern = r'(^|\s)([ауоиэыяюеёАУОИЭЫЯЮЕЁaeiouyAEIOUY]\w*)'

    def replace_match(match):
        replacement = random.choice(replacement_words)
        return match.group(1) + replacement

    return re.sub(vowel_pattern, replace_match, text, flags=re.IGNORECASE | re.UNICODE)


def get_recent_songs(limit=6):
    db_sess = db_session.create_session()
    songs = db_sess.query(Song).order_by(Song.created_date.desc()).limit(limit).all()
    db_sess.close()
    return songs


def get_top_users(limit=5):
    db_sess = db_session.create_session()
    top_users = db_sess.query(User, func.count(Annotation.id).label('annotation_count')) \
        .join(Annotation, User.id == Annotation.user_id) \
        .group_by(User.id) \
        .order_by(func.count(Annotation.id).desc()) \
        .limit(limit) \
        .all()
    db_sess.close()
    return top_users


@app.route('/')
def index():
    songs = get_recent_songs()
    top_users = get_top_users()
    return render_template('index.html', title='Главная страница', songs=songs, top_users=top_users)


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
        if form.file.data:
            file_data = form.file.data.read().decode('utf-8')
            form.lyrics.data = file_data

        track_id, album_id = find_yandex_track(form.title.data, form.artist.data)

        db_sess = db_session.create_session()
        song = Song(
            title=form.title.data,
            artist=form.artist.data,
            lyrics=censor_vowel_words(form.lyrics.data),
            user_id=current_user.id,
            created_date=datetime.utcnow(),
            track_id=track_id,
            album_id=album_id
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

api.add_resource(SongFullSearchResource, '/api/full_song_search')
api.add_resource(SongListResource, '/api/song')
api.add_resource(SongResource, '/api/song/<int:song_id>')


if __name__ == '__main__':
    db_session.global_init('db/users.db')
    seed_test_data()
    app.run(port=8080, host='127.0.0.1', debug=True)