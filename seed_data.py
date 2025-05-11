from data.db_session import create_session
from data.users import User
from data.songs import Song, Annotation
from datetime import datetime
import re
import random


def censor_vowel_words(text):
    if not text:
        return text
    replacement_words = ['СВАГА', 'ДРИПЧИК', 'МАЙОНЕЗ', 'КАРТЕЛЬ', 'ЧУВАААААК']
    vowel_pattern = r'(^|\s)([ауоиэыяюеёАУОИЭЫЯЮЕЁaeiouyAEIOUY]\w*)'

    def replace_match(match):
        replacement = random.choice(replacement_words)
        return match.group(1) + replacement

    return re.sub(vowel_pattern, replace_match, text, flags=re.IGNORECASE | re.UNICODE)


def seed_test_data():
    db_sess = create_session()

    try:

        if db_sess.query(User).count() > 0:
            return False

        users = [
            User(name="Токсик", email="toxic@example.com", about="Лягушка с саундклауда"),
            User(name="Крош", email="krosh@example.com", about="Смешарик-репер"),
            User(name="Нюша", email="nyusha@example.com", about="Поп-дива из смешариков"),
            User(name="Админ", email="admin@non-genius.com", about="Создатель сайта"),
            User(name="Аноним", email="anon@example.com", about="Тайный поклонник Макана")
        ]

        for user in users:
            user.set_password("123456")
            db_sess.add(user)

        db_sess.commit()

        songs_data = [
            {
                "title": "Лягушачий реп",
                "artist": "Токсик",
                "lyrics": "Я просто лягушка\nКва-ква-ква\nНа саундклауде\nМоя тусовка\nА я всё плыву\nИ пою про любовь"
            },
            {
                "title": "Свага на районе",
                "artist": "Крош",
                "lyrics": "Эй, это Крош\nЯ кручу-верчу\nА у меня есть\nСвага в кармане\nИ я летаю\nНад всеми на свете"
            },
            {
                "title": "Розовые сны",
                "artist": "Нюша",
                "lyrics": "Ой, какие сны\nРозовые они\nА я лечу\nНад облаками\nИ пою про\nСчастье и радость"
            },
            {
                "title": "Non-Genius Anthem",
                "artist": "Админ",
                "lyrics": "Мы не гении\nНо мы стараемся\nА наш сайт\nЛучший в мире\nИ мы гордимся\nЭтим очень"
            },
            {
                "title": "Тайный фанат",
                "artist": "Аноним",
                "lyrics": "Я люблю артиста\nНо вам не скажу\nЭто секрет\nМежду нами\nА он даже\nНе знает об этом"
            }
        ]

        for i, song_data in enumerate(songs_data, 1):
            censored_lyrics = censor_vowel_words(song_data["lyrics"])
            song = Song(
                title=song_data["title"],
                artist=song_data["artist"],
                lyrics=censored_lyrics,
                user_id=i,
                created_date=datetime.now()
            )
            db_sess.add(song)

        db_sess.commit()

        annotations = [
            {
                "text": "Здесь автор использует метафору лягушки",
                "user_id": 4,
                "song_id": 1
            },
            {
                "text": "Свага - это важный элемент в тексте",
                "user_id": 1,
                "song_id": 2
            },
            {
                "text": "Розовый цвет символизирует нежность",
                "user_id": 3,
                "song_id": 3
            },
            {
                "text": "Гимн сайта должен быть у всех на устах",
                "user_id": 4,
                "song_id": 4
            },
            {
                "text": "Тайный поклонник всегда остаётся в тени",
                "user_id": 5,
                "song_id": 5
            }
        ]

        for annotation in annotations:
            anno = Annotation(
                text=annotation["text"],
                user_id=annotation["user_id"],
                song_id=annotation["song_id"],
                created_at=datetime.now()
            )
            db_sess.add(anno)

        db_sess.commit()
        return True

    except Exception as e:
        db_sess.rollback()
        print(f"Ошибка при заполнении тестовыми данными: {e}")
        return False
    finally:
        db_sess.close()
