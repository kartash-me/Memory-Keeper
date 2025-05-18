import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session

from functions import dotenv


SqlAlchemyBase = orm.declarative_base()
__factory = None


def global_init():
    global __factory

    if __factory:
        return

    data = {
        key: dotenv(key.upper())
        for key in ["engine", "user", "password", "host", "port", "database"]
    }
    db = "{engine}://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4".format(
        **data
    )
    #db = f"mysql+pymysql://u3120708_kartash:AKartash0505@server284.hosting.reg.ru:3306/u3120708_memory_keeper?charset=utf8mb4"
    #Это если dotenv не будет работать
    engine = sa.create_engine(db, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from data import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()
