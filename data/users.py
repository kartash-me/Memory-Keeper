import sqlalchemy as sa
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash

from data.db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = "users"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    email = sa.Column(sa.String(255), index=True, unique=True, nullable=False)
    hashed_password = sa.Column(sa.String(255), nullable=True)
    login = sa.Column(sa.String(255), unique=True, nullable=False)
    number = sa.Column(sa.String(255), unique=True, nullable=False)
    avatar = sa.Column(sa.String(255), nullable=True)
    name = sa.Column(sa.String(255), nullable=True)
    surname = sa.Column(sa.String(255), nullable=True)
    date_of_birth = sa.Column(sa.Date, nullable=True)
    used_space = sa.Column(sa.Integer, default=0, nullable=False)
    date_of_registration = sa.Column(sa.Date, nullable=False)

    photos = relationship("Photo", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
