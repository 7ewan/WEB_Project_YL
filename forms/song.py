from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired


class SongForm(FlaskForm):
    title = StringField('Название песни', validators=[DataRequired()])
    artist = StringField('Исполнитель', validators=[DataRequired()])
    lyrics = TextAreaField('Текст песни', validators=[DataRequired()])
    submit = SubmitField('Добавить песню')