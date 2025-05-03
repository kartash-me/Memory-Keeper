from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from data.db_session import SqlAlchemyBase


class Photo(SqlAlchemyBase):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    location = Column(String, nullable=True)  # координаты: широта, долгота
    timestamp = Column(DateTime)  # время создания фото
    file_path = Column(String, nullable=False)  # путь к файлу
    user_id = Column(Integer, ForeignKey("users.id"))  # связь с пользователем

    user = relationship("User", back_populates="photos")
