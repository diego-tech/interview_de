from sqlalchemy import create_engine

def init_engine(db_url: str):
    if not db_url:
        raise ValueError("DATABASE_URL no proporcionada")
    return create_engine(db_url)
