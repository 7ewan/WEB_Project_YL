from flask_restful import Resource, reqparse
from data import db_session
from data.songs import Song
import yandex_music

full_search_parser = reqparse.RequestParser()
full_search_parser.add_argument('title', required=True)
full_search_parser.add_argument('artist', required=True)

class SongFullSearchResource(Resource):
    def post(self):
        args = full_search_parser.parse_args()
        title = args['title']
        artist = args['artist']

        db_sess = db_session.create_session()
        songs = db_sess.query(Song).filter(
            (Song.title.ilike(f'%{title}%')) &
            (Song.artist.ilike(f'%{artist}%'))
        ).all()

        our_results = []
        for song in songs:
            our_results.append({
                'id': song.id,
                'title': song.title,
                'artist': song.artist,
                'lyrics': song.lyrics,
                'views': song.views,
                'created_date': song.created_date.isoformat()
            })

        client = yandex_music.Client().init()
        search_text = f"{artist} {title}"
        search_result = client.search(search_text)

        yandex_results = []
        if search_result.tracks and search_result.tracks.results:
            for track in search_result.tracks.results[:5]:
                yandex_results.append({
                    'title': track.title,
                    'artist': ', '.join([a.name for a in track.artists]),
                    'track_id': track.id,
                    'album_id': track.albums[0].id if track.albums else None,
                    'duration_ms': track.duration_ms
                })

        return {
            'our_songs': our_results,
            'yandex_songs': yandex_results
        }
