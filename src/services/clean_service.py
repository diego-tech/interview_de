import pandas as pd
import re

REQUIRED = ("title", "description", "publishedAt")

def clean_raw_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Espera columnas: 
    ['author','title','description','url','urlToImage','publishedAt','content','source_id','source_name']
    Reglas:
      - author vacío -> 'Anonimo'
      - title/description/publishedAt obligatorios
      - publishedAt -> datetime (UTC)
      - dedupe por url
    Devuelve columnas normalizadas y ordenadas.
    """
    if df_raw is None or df_raw.empty:
        return pd.DataFrame(columns=[
            "url","title","description","content","author",
            "published_at","urlToImage","source_id","source_name"
        ])

    df = df_raw.copy()

    # Autor por defecto
    if "author" not in df.columns:
        df["author"] = "Anonimo"
    else:
        df["author"] = df["author"].fillna("").astype(str).str.strip()
        df.loc[df["author"] == "", "author"] = "Anonimo"

    # Asegurar obligatorios existan
    for c in REQUIRED:
        if c not in df.columns:
            df[c] = pd.NA

    # Normalizar fecha
    df["publishedAt"] = pd.to_datetime(df["publishedAt"], errors="coerce", utc=True)

    # Filtrar filas inválidas (obligatorios)
    mask_ok = (
        df["title"].fillna("").astype(str).str.strip().ne("") &
        df["description"].fillna("").astype(str).str.strip().ne("") &
        df["publishedAt"].notna()
    )
    df = df[mask_ok].copy()

    # Deduplicado por URL
    if "url" in df.columns:
        df = df.drop_duplicates(subset="url", keep="first")

    # Renombrado final
    df = df.rename(columns={"publishedAt": "published_at"})

    # Orden de columnas
    cols = ["url","title","description","content","author","published_at","urlToImage","source_id","source_name"]
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA
    return df[cols].reset_index(drop=True)

def extract_extra_chars(content: str) -> int:
    """
    Extrae el número de caracteres adicionales del formato '[+XXXX chars]'.
    Si no existe, devuelve 0.
    """
    if not isinstance(content, str):
        return 0
    match = re.search(r"\[\+(\d+)\s+chars\]", content)
    return int(match.group(1)) if match else 0

def filter_by_min_length(df: pd.DataFrame, min_total_chars=800) -> pd.DataFrame:
    df = df.copy()
    df["extra_chars"] = df["content"].apply(extract_extra_chars)
    df["content_len"] = df["content"].fillna("").str.len() + df["extra_chars"]
    return df[df["content_len"] >= min_total_chars].reset_index(drop=True)
