from typing import Tuple, Optional
import requests
import pandas as pd


def fetch_ai_marketing_news(api_url: str, params: dict) -> Tuple[Optional[pd.DataFrame], dict]:
    """
    Llama a la API de NewsAPI para obtener noticias de AI y Marketing.
    
    Args:
        api_url (str): URL base del endpoint (ej: https://newsapi.org/v2/everything).
        params (dict): Diccionario de parámetros que incluye apiKey y q.
    
    Returns:
        Tuple[Optional[pd.DataFrame], dict]:
            - DataFrame con artículos o None si hay error.
            - Diccionario con metadatos de la respuesta (status, totalResults, error_message si aplica).
    
    Nota profesional:
        El consumo de APIs externas se centraliza aquí para:
        - Facilitar pruebas (mock de requests).
        - Evitar repetir lógica de manejo de errores.
        - Mantener desacoplada la construcción de queries (que se hace en utils/query_builder.py).
    """
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return None, {
            "status": "error",
            "error_message": f"Error de conexión: {str(e)}"
        }

    try:
        data = response.json()
    except ValueError:
        return None, {
            "status": "error",
            "error_message": "La respuesta no es un JSON válido."
        }

    status = data.get("status", "error")
    if status != "ok":
        return None, {
            "status": status,
            "error_message": data.get("message", "Error desconocido en la API.")
        }

    total_results = data.get("totalResults", 0)
    articles = data.get("articles", [])

    if not articles:
        return pd.DataFrame(), {
            "status": status,
            "totalResults": total_results
        }

    # Normalización a DataFrame
    news_df = pd.json_normalize(articles)
    news_df = news_df.rename(columns={
        "source.id": "source_id",
        "source.name": "source_name"
    })

    return news_df, {
        "status": status,
        "totalResults": total_results
    }
