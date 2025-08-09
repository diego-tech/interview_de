import pandas as pd
import re

# Columnas que son obligatorias para que un registro se considere válido
REQUIRED = ("title", "description", "publishedAt", "url")

def clean_raw_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y normaliza los datos crudos recibidos de la API.
    
    Reglas aplicadas:
      - Rellena 'author' vacío con 'Anonimo'
      - Verifica que 'title', 'description' y 'publishedAt' estén presentes
      - Convierte 'publishedAt' a datetime UTC
      - Normaliza URLs y genera un hash único para deduplicar
      - Elimina registros sin URL o sin campos obligatorios
      - Trunca el contenido a 20.000 caracteres para evitar payloads grandes
    
    Args:
        df_raw (pd.DataFrame): DataFrame crudo con columnas como:
            ['author','title','description','url','urlToImage',
             'publishedAt','content','source_id','source_name']
    
    Returns:
        pd.DataFrame: DataFrame limpio y normalizado, con columnas ordenadas.
    """
    cols_out = [
        "url", "title", "description", "content", "author",
        "published_at", "url_to_image", "source_id", "source_name"
    ]

    if df_raw is None or df_raw.empty:
        return pd.DataFrame(columns=cols_out)

    df = df_raw.copy()

    # Asegurar columnas obligatorias
    for c in REQUIRED:
        if c not in df.columns:
            df[c] = pd.NA

    # Limpiar espacios y nulos en columnas clave
    for c in ["title", "description", "content", "author", "url", "urlToImage", "source_id", "source_name"]:
        if c in df.columns:
            df[c] = df[c].fillna("").astype(str).str.strip()

    # Rellenar autores vacíos
    if "author" not in df.columns:
        df["author"] = "Anonimo"
    df.loc[df["author"] == "", "author"] = "Anonimo"

    # Eliminar filas sin URL y eliminar url duplicadas
    df = df[df["url"] != ""].copy()
    df = df.drop_duplicates(subset=["url"])

    # Convertir fechas a UTC
    df["publishedAt"] = pd.to_datetime(df["publishedAt"], errors="coerce", utc=True)

    # Filtrar registros sin campos obligatorios
    mask_ok = (
        df["title"].ne("") &
        df["description"].ne("") &
        df["publishedAt"].notna()
    )
    df = df[mask_ok].copy()

    # Limitar tamaño del contenido
    if "content" in df.columns:
        df["content"] = df["content"].str.slice(0, 20000)

    # Renombrar columnas
    df = df.rename(columns={"publishedAt": "published_at", "urlToImage": "url_to_image"})

    # Asegurar que todas las columnas de salida existan
    for c in cols_out:
        if c not in df.columns:
            df[c] = pd.NA

    return df[cols_out].reset_index(drop=True)

def extract_extra_chars(content: str) -> int:
    """
    Extrae el número de caracteres adicionales del formato '[+XXXX chars]'
    que aparece en algunos textos de NewsAPI.
    
    Args:
        content (str): Texto del contenido del artículo.
    
    Returns:
        int: Número de caracteres adicionales, 0 si no aplica.
    """
    if not isinstance(content, str):
        return 0
    m = re.search(r"\[\+(\d+)\s+chars\]", content)
    return int(m.group(1)) if m else 0

def filter_by_min_length(df: pd.DataFrame, min_total_chars: int = 800) -> pd.DataFrame:
    """
    Filtra artículos cuyo contenido total (texto + caracteres extra) 
    sea inferior al mínimo requerido.
    
    Args:
        df (pd.DataFrame): DataFrame con columna 'content'.
        min_total_chars (int): Mínimo de caracteres totales requeridos.
    
    Returns:
        pd.DataFrame: DataFrame filtrado.
    """
    if df is None or df.empty:
        return df

    df = df.copy()
    df["extra_chars"] = df["content"].apply(extract_extra_chars)
    df["content_len"] = df["content"].fillna("").str.len() + df["extra_chars"]
    
    return df[df["content_len"] >= min_total_chars].reset_index(drop=True)
