from flask_restful import Resource, reqparse
from data import db_session
from data.songs import Song
from datetime import datetime

song_parser = reqparse.RequestParser()
song_parser.add_argument('title', required=True)
song_parser.add_argument('artist', required=True)
song_parser.add_argument('lyrics', required=True)

class SongListResource(Resource):
    def get(self):
        db_sess = db_session.create_session()
        songs = db_sess.query(Song).all()
        return [{
            'id': song.id,
            'title': song.title,
            'artist': song.artist,
            'lyrics': song.lyrics,
            'views': song.views,
            'created_date': song.created_date.isoformat()
        } for song in songs]

    def post(self):
        args = song_parser.parse_args()
        db_sess = db_session.create_session()
        song = Song(
            title=args['title'],
            artist=args['artist'],
            lyrics=args['lyrics'],
            created_date=datetime.utcnow(),
            views=0
        )
        db_sess.add(song)
        db_sess.commit()
        return {'message': 'Песня добавлена', 'id': song.id}, 201


class SongResource(Resource):
    def get(self, song_id):
        db_sess = db_session.create_session()
        song = db_sess.query(Song).get(song_id)
        if not song:
            return {'error': 'Песня не найдена'}, 404
        return {
            'id': song.id,
            'title': song.title,
            'artist': song.artist,
            'lyrics': song.lyrics,
            'views': song.views,
            'created_date': song.created_date.isoformat()
        }

    def put(self, song_id):
        args = song_parser.parse_args()
        db_sess = db_session.create_session()
        song = db_sess.query(Song).get(song_id)
        if not song:
            return {'error': 'Песня не найдена'}, 404
        song.title = args['title']
        song.artist = args['artist']
        song.lyrics = args['lyrics']
        db_sess.commit()
        return {'message': 'Песня обновлена'}

    def delete(self, song_id):
        db_sess = db_session.create_session()
        song = db_sess.query(Song).get(song_id)
        if not song:
            return {'error': 'Песня не найдена'}, 404
        db_sess.delete(song)
        db_sess.commit()
        return {'message': 'Песня удалена'}
