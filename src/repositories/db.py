from sqlalchemy import create_engine, text
from .news import metadata  # Importa el objeto metadata para crear tablas con create_all

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


def ensure_schema(engine):
    """
    Garantiza que el esquema de base de datos y restricciones necesarias existen.

    Acciones:
        1. Crea las tablas definidas en metadata si no existen (idempotente).
        2. Verifica la existencia del constraint único en `news.url_hash`.
           Si no existe, lo crea.

    Parámetros:
        engine (sqlalchemy.engine.Engine): Conexión a la base de datos.

    Uso:
        ensure_schema(engine)

    Nota:
        Este método es útil para entornos donde se despliega el proyecto sin migraciones
        automáticas y se necesita garantizar la integridad de datos.
    """
    # Crea las tablas declaradas en metadata (si no existen)
    metadata.create_all(engine)

    # Comprueba y crea el índice único si no está definido
    with engine.begin() as conn:
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint
                    WHERE conname = 'uq_news_url_hash'
                ) THEN
                    ALTER TABLE news
                    ADD CONSTRAINT uq_news_url_hash UNIQUE (url_hash);
                END IF;
            END $$;
        """))
