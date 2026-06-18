from sqlalchemy import create_engine

DATABASE_URL = "mysql+pymysql://username:password@localhost:3306/dbname"

engine = create_engine(
    DATABASE_URL,
    echo=True
)
# use it as dependency
def get_conn():
    with engine.begin() as conn:
        yield conn
