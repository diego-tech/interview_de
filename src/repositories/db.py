from sqlalchemy import create_engine, text

def init_engine(db_url: str):
    """
    Inicializa el motor de conexión SQLAlchemy a la base de datos.

    Parámetros:
        db_url (str): Cadena de conexión a la base de datos en formato SQLAlchemy.
                      Ejemplo: 'postgresql+psycopg2://user:password@host:port/dbname'

    Retorna:
        sqlalchemy.engine.Engine: Objeto Engine configurado.

    Lanza:
        ValueError: Si no se proporciona una URL de conexión válida.

    Uso:
        engine = init_engine(DATABASE_URL)
    """
    if not db_url:
        raise ValueError("DATABASE_URL no proporcionada")
    return create_engine(db_url)
