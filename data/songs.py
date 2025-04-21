from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase


class Song(SqlAlchemyBase):
    __tablename__ = 'songs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    lyrics = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User")
