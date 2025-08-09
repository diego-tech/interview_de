-- Creación de la tabla donde se almacenará la información extraída de NewsAPI
CREATE TABLE IF NOT EXISTS news (
  id            BIGSERIAL PRIMARY KEY,
  url           TEXT UNIQUE NOT NULL,         
  source_id     TEXT,
  source_name   TEXT,
  author        TEXT,
  title         TEXT,
  description   TEXT,
  content       TEXT,
  url_to_image  TEXT,
  published_at  TIMESTAMPTZ,                     
);

-- Índices útiles para consultas y ordenamiento
CREATE INDEX IF NOT EXISTS idx_news_raw_published_at ON news (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_raw_source_name   ON news (source_name);