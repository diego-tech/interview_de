from typing import List, Dict, Optional
from itertools import product
from collections import defaultdict

from sqlalchemy import Engine
from sqlalchemy import text


def quote_term(t: str) -> str:
    """
    Si el término contiene espacios, lo envuelve entre comillas y elimina espacios.
    Esto asegura búsquedas exactas en NewsAPI.
    """
    t = t.strip()
    return f'"{t}"' if " " in t else t

def chunk_list(lst: List[str], max_len: int) -> List[List[str]]:
    """
    Divide la lista de términos en sublistas cuya longitud total
    (en caracteres) no exceda max_len.
    Esto evita que el parámetro `q` supere los 500 caracteres en NewsAPI (Error identificado The complete value for q must be URL-encoded. Max length: 500 chars.).
    """
    chunks = []
    current = []
    length = 0

    for item in lst:
        token = quote_term(item)
        token_len = len(token) + 4  # Contamos " OR " como 4 caracteres
        if length + token_len > max_len and current:
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
    Prepara bloques (OR-clauses) por categoría aplicando chunking para no superar el límite de caracteres.
    - groups: dict {categoria: [terminos ya quoteados y con NOT si procede]}
    - max_chars: límite total del parámetro q (NewsAPI = 500)
    - categories: orden explícito de categorías a usar (si None, usa todas las keys de groups)
    Devuelve un dict {categoria: [ "(t1 OR t2 ...)", "(...)" , ... ]}
    """
    if categories is None:
        categories = list(groups.keys())
    if not categories:
        raise ValueError("No hay categorías para construir la query.")

    # Estimación simple: repartimos el presupuesto entre categorías
    per_cat_budget = max(50, max_chars // max(1, len(categories)))  # mínimo 50 por bloque/categoría

    blocks = {}
    for cat in categories:
        terms = groups.get(cat, [])
        if not terms:
            raise ValueError(f"No hay términos activos para la categoría '{cat}'.")

        # Partimos la lista de términos de esta categoría en trozos que quepan en su presupuesto
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
    Combina un bloque por categoría con AND (producto cartesiano) y filtra
    las combinaciones que superen 'max_chars'.
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
    Lee keywords activas desde la BD y construye una o varias queries <= max_chars
    usando bloques por categoría y combinándolos con AND.
    - max_chars: límite del parámetro `q` (NewsAPI = 500)
    - categories: orden/selección de categorías a usar (por defecto, todas las encontradas)
    Devuelve: lista de strings `q` listas para usar en /v2/everything.
    """
    sql = """
    SELECT term, category, negate
    FROM news_keywords
    WHERE active = TRUE
    """

    # 1) Leer términos y agrupar por categoría, dejando cada término "listo" (quoted y con NOT si aplica)
    groups: Dict[str, List[str]] = defaultdict(list)
    with engine.connect() as conn:
        for term, category, negate in conn.execute(text(sql)):
            token = quote_term(term.strip())
            token = f'NOT {token}' if negate else token
            groups[category].append(token)

    if not groups:
        raise ValueError("No hay keywords activas en la base de datos.")

    # 2) Si no se especifica orden/conjunto de categorías, usamos todas las presentes
    cats_order = categories or list(groups.keys())

    # 3) Construir bloques por categoría con chunking interno
    blocks_by_cat = build_blocks_by_category(groups, max_chars=max_chars, categories=cats_order)

    # 4) Combinar bloques (producto cartesiano) asegurando q <= max_chars
    queries = build_queries_from_blocks(blocks_by_cat, max_chars=max_chars, categories=cats_order)

    if not queries:
        raise ValueError("No se pudo construir ninguna query dentro del límite de caracteres.")

    return queries

