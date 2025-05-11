from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from data.db_session import SqlAlchemyBase


class Photo(SqlAlchemyBase):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    location = Column(String, nullable=True)  # координаты: широта, долгота
    timestamp = Column(DateTime)  # время создания фото
    filename = Column(String, nullable=False)  # имя файла
    user_id = Column(Integer, ForeignKey("users.id"))  # связь с пользователем

    user = relationship("User", back_populates="photos")
