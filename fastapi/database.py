from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./blog.db"
# this /// means this local db file and

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#dependency for routes 
def get_db():
    with SessionLocal() as db:
        yield db

# optional so far i know 
class Base(DeclarativeBase):
    pass
