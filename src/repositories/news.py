from sqlalchemy import Table, Column, BigInteger, Text, DateTime, MetaData, UniqueConstraint

metadata = MetaData()

news = Table(
    "news", metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("url", Text, nullable=False),
    Column("source_id", Text),
    Column("description", Text),
    Column("content", Text),
    Column("author", Text),
    Column("url_to_image", Text),
    Column("published_at", DateTime(timezone=True)),
    Column("source_name", Text, nullable=False),
    Column("title", Text),
    UniqueConstraint("url", name="uq_news_url"),
)

def upsert_news_bulk(engine, df) -> int:
    """
    Inserta los registros limpios y filtrados de la API en la base de datos

    Parámetros:
        engine: Motor de conexión de SQLAlchemy
        df: DataFrame con la información que debe de ser insertada
    
    Returns:
        Lóngitud de filas insertadas en la Base de Datos
    """
    if df is None or df.empty:
        return 0

    rows = []
    for r in df.to_dict(orient="records"):
        rows.append({
            "url":          r.get("url"),
            "source_id":    r.get("source_id"),
            "description":  r.get("description"),
            "content":      r.get("content"),
            "author":       r.get("author"),
            "url_to_image": r.get("url_to_image"),
            "published_at": r.get("published_at"),
            "source_name":  r.get("source_name") or "",
            "title":        r.get("title")
        })

    from sqlalchemy.dialects.postgresql import insert as pg_insert
    stmt = pg_insert(news).values(rows)
    update_cols = {
        "source_id":    stmt.excluded.source_id,
        "description":  stmt.excluded.description,
        "content":      stmt.excluded.content,
        "author":       stmt.excluded.author,
        "url_to_image": stmt.excluded.url_to_image,
        "published_at": stmt.excluded.published_at,
        "source_name":  stmt.excluded.source_name,
        "title":        stmt.excluded.title
    }
    upsert = stmt.on_conflict_do_update(index_elements=["url"], set_=update_cols)

    with engine.begin() as conn:
        conn.execute(upsert)
    return len(rows)