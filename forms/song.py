from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired

class SongForm(FlaskForm):
    title = StringField('Название песни', validators=[DataRequired()])
    artist = StringField('Исполнитель', validators=[DataRequired()])
    lyrics = TextAreaField('Текст песни', validators=[DataRequired()])
    file = FileField('Загрузить текст из .txt', validators=[FileAllowed(['txt'], 'Только .txt файлы!')])
    submit = SubmitField('Добавить')
