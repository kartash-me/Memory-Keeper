from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import relationship

from data.db_session import SqlAlchemyBase


class Photo(SqlAlchemyBase):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(String, nullable=True)
    timestamp = Column(DateTime)  # время создания фото
    filename = Column(String, nullable=False)  # имя файла
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # связь с пользователем

    user = relationship("User", back_populates="photos")
