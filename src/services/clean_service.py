import pandas as pd
import re
import hashlib
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

REQUIRED = ("title", "description", "publishedAt")
TRACKING_PARAMS = {
    "utm_source","utm_medium","utm_campaign","utm_term","utm_content",
    "utm_id","utm_source_platform","gclid","fbclid"
}

def normalize_url(u: str) -> str:
    if not u:
        return u
    sp = urlsplit(u)
    # limpia query de tracking y quita fragmento
    q = [(k, v) for k, v in parse_qsl(sp.query, keep_blank_values=True)
         if k.lower() not in TRACKING_PARAMS]
    sp = sp._replace(netloc=sp.netloc.lower(), query=urlencode(q, doseq=True), fragment="")
    return urlunsplit(sp)

def clean_raw_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Espera columnas: 
    ['author','title','description','url','urlToImage','publishedAt','content','source_id','source_name']
    Reglas:
      - author vacío -> 'Anonimo'
      - title/description/publishedAt obligatorios
      - publishedAt -> datetime (UTC)
      - dedupe por url normalizada (hash)
      - truncado de content para evitar payloads gigantes
    Devuelve columnas normalizadas y ordenadas.
    """
    cols_out = ["url","url_hash","title","description","content","author",
                "published_at","url_to_image","source_id","source_name"]

    if df_raw is None or df_raw.empty:
        return pd.DataFrame(columns=cols_out)

    df = df_raw.copy()

    # Asegurar obligatorios existan
    for c in REQUIRED:
        if c not in df.columns:
            df[c] = pd.NA

    # Normalizar strings básicos
    for c in ["title","description","content","author","url","urlToImage","source_id","source_name"]:
        if c in df.columns:
            df[c] = df[c].fillna("").astype(str).str.strip()

    # Autor por defecto
    if "author" not in df.columns:
        df["author"] = "Anonimo"
    df.loc[df["author"] == "", "author"] = "Anonimo"

    # URL normalizada + hash (descarta sin URL)
    df = df[df["url"] != ""].copy()
    df["url_norm"] = df["url"].map(normalize_url)
    df["url_hash"] = df["url_norm"].fillna("").map(lambda x: hashlib.sha1(x.lower().encode("utf-8")).hexdigest())
    df = df.drop_duplicates(subset=["url_hash"])

    # Fecha a UTC
    df["publishedAt"] = pd.to_datetime(df["publishedAt"], errors="coerce", utc=True)

    # Filtrar obligatorios válidos
    mask_ok = (
        df["title"].ne("") &
        df["description"].ne("") &
        df["publishedAt"].notna()
    )
    df = df[mask_ok].copy()

    # Truncado de contenido (por si vienen tochos)
    if "content" in df.columns:
        df["content"] = df["content"].str.slice(0, 20000)

    # Renombrado final
    df = df.rename(columns={"publishedAt": "published_at", "urlToImage": "url_to_image"})

    # Asegurar columnas de salida
    for c in cols_out:
        if c not in df.columns:
            df[c] = pd.NA

    return df[cols_out].reset_index(drop=True)

def extract_extra_chars(content: str) -> int:
    """
    Extrae el número de caracteres adicionales del formato '[+XXXX chars]'.
    Si no existe, devuelve 0.
    """
    if not isinstance(content, str):
        return 0
    m = re.search(r"\[\+(\d+)\s+chars\]", content)
    return int(m.group(1)) if m else 0

def filter_by_min_length(df: pd.DataFrame, min_total_chars: int = 800) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    df = df.copy()
    df["extra_chars"] = df["content"].apply(extract_extra_chars)
    df["content_len"] = df["content"].fillna("").str.len() + df["extra_chars"]
    return df[df["content_len"] >= min_total_chars].reset_index(drop=True)
