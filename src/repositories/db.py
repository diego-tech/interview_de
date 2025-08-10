from sqlalchemy import create_engine

def init_engine(db_url: str):
    """
    Inicializa el motor de conexión SQLAlchemy a la base de datos.

    Parámetros:
        db_url (str): Cadena de conexión a la base de datos en formato SQLAlchemy.

    Returns:
        sqlalchemy.engine.Engine: Objeto Engine configurado.
    """
    if not db_url:
        raise ValueError("DATABASE_URL no proporcionada")
    return create_engine(db_url)
