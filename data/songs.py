from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey


class Annotation(SqlAlchemyBase):
    __tablename__ = 'annotations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'))
    song_id = Column(Integer, ForeignKey('songs.id'))

    user = relationship("User")


class Song(SqlAlchemyBase):
    __tablename__ = 'songs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    lyrics = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    annotations = relationship("Annotation", backref="song", cascade="all, delete-orphan")