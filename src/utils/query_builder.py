from typing import List, Dict, Optional
from itertools import product
from collections import defaultdict

from sqlalchemy import Engine, text

def quote_term(t: str) -> str:
    """
    Envuelve un término entre comillas si contiene espacios, asegurando
    que NewsAPI lo interprete como una búsqueda exacta.
    
    Args:
        t (str): término original.
    
    Returns:
        str: término preparado para ser usado en la query.
    """
    t = t.strip()
    return f'"{t}"' if " " in t else t

def chunk_list(lst: List[str], max_len: int) -> List[List[str]]:
    """
    Divide una lista de términos en sublistas cuya longitud total estimada
    (incluyendo separadores " OR ") no supere `max_len` caracteres.
    
    Esto evita superar el límite de 500 caracteres del parámetro `q` en NewsAPI.
    
    Args:
        lst (List[str]): lista de términos de búsqueda.
        max_len (int): límite máximo de caracteres para cada bloque.
    
    Returns:
        List[List[str]]: lista de sublistas con términos que respetan el límite.
    """
    chunks = []
    current = []
    length = 0

    for item in lst:
        token = quote_term(item)
        token_len = len(token) + 4  # +4 por " OR "
        
        if length + token_len > max_len and current:
            # Inicia un nuevo bloque
            chunks.append(current)
            current = [item]
            length = token_len
        else:
            current.append(item)
            length += token_len

    if current:
        chunks.append(current)

    return chunks

def build_blocks_by_category(groups: Dict[str, List[str]], max_chars: int, categories: List[str] = None) -> Dict[str, List[str]]:
    """
    Construye bloques de términos por categoría, aplicando `chunk_list` para
    evitar que cada bloque supere el presupuesto de caracteres asignado.
    
    Args:
        groups (dict): {categoria: [términos quoteados o con NOT]}
        max_chars (int): límite total del parámetro `q`.
        categories (List[str], opcional): orden y selección de categorías a usar.
    
    Returns:
        dict: {categoria: ["(term1 OR term2)", "(...)", ...]}
    """
    if categories is None:
        categories = list(groups.keys())
    if not categories:
        raise ValueError("No hay categorías para construir la query.")

    # Presupuesto estimado por categoría
    per_cat_budget = max(50, max_chars // max(1, len(categories)))

    blocks = {}
    for cat in categories:
        terms = groups.get(cat, [])
        if not terms:
            raise ValueError(f"No hay términos activos para la categoría '{cat}'.")

        # Divide en chunks que respeten el presupuesto
        cat_chunks = chunk_list(terms, per_cat_budget)
        cat_blocks = [ "(" + " OR ".join(chunk) + ")" for chunk in cat_chunks ]
        blocks[cat] = cat_blocks

    return blocks

def build_queries_from_blocks(
    blocks_by_cat: Dict[str, List[str]],
    max_chars: int,
    categories: List[str]
) -> List[str]:
    """
    Combina los bloques de cada categoría con AND (producto cartesiano)
    y filtra las combinaciones que superen el límite de caracteres.
    
    Args:
        blocks_by_cat (dict): bloques por categoría.
        max_chars (int): límite máximo permitido en `q`.
        categories (List[str]): orden de categorías a combinar.
    
    Returns:
        List[str]: lista de queries finales válidas para NewsAPI.
    """
    if not categories:
        categories = list(blocks_by_cat.keys())

    queries: List[str] = []
    for combo in product(*[blocks_by_cat[cat] for cat in categories]):
        q = " AND ".join(combo)
        if len(q) <= max_chars:
            queries.append(q)

    if not queries:
        raise ValueError("No se pudo generar ninguna query <= max_chars; reduce términos o ajusta el reparto.")
    
    return queries

def build_q_from_db(engine: Engine, max_chars: int = 500, categories: List[str] = None) -> List[str]:
    """
    Extrae términos activos de la base de datos y construye queries listas
    para usar en `/v2/everything` de NewsAPI.
    
    Flujo:
      1. Lee términos activos desde `news_keywords` (solo 'en').
      2. Agrupa por categoría y aplica formato (quote y/o NOT).
      3. Construye bloques por categoría respetando límites.
      4. Genera todas las combinaciones posibles (producto cartesiano).
      5. Filtra combinaciones que superen `max_chars`.
    
    Args:
        engine (Engine): conexión SQLAlchemy a la base de datos.
        max_chars (int): límite de caracteres por query (NewsAPI = 500).
        categories (List[str], opcional): orden o filtro de categorías a usar.
    
    Returns:
        List[str]: queries listas para enviar a la API.
    """
    sql = """
    SELECT term, category, negate
    FROM news_keywords
    WHERE active = TRUE AND lang = 'en'
    """

    groups: Dict[str, List[str]] = defaultdict(list)
    with engine.connect() as conn:
        for term, category, negate in conn.execute(text(sql)):
            token = quote_term(term.strip())
            token = f'NOT {token}' if negate else token
            groups[category].append(token)

    if not groups:
        raise ValueError("No hay keywords activas en la base de datos.")

    cats_order = categories or list(groups.keys())

    blocks_by_cat = build_blocks_by_category(groups, max_chars=max_chars, categories=cats_order)
    queries = build_queries_from_blocks(blocks_by_cat, max_chars=max_chars, categories=cats_order)

    if not queries:
        raise ValueError("No se pudo construir ninguna query dentro del límite de caracteres.")

    return queries
