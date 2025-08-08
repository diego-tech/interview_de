-- Tabla RAW: almacena la respuesta original de la API + metadatos mínimos
CREATE TABLE IF NOT EXISTS news_raw (
  id            BIGSERIAL PRIMARY KEY,
  url           TEXT UNIQUE NOT NULL,              -- dedupe por URL
  source_id     TEXT,
  source_name   TEXT,
  author        TEXT,
  title         TEXT,
  description   TEXT,
  content       TEXT,
  url_to_image  TEXT,
  published_at  TIMESTAMPTZ,                       -- viene en UTC (Z)
  payload       JSONB NOT NULL,                    -- objeto crudo tal cual devuelve la API
  fetched_at    TIMESTAMPTZ NOT NULL DEFAULT NOW() -- momento de ingesta
);

-- Índices útiles para consultas y ordenamiento
CREATE INDEX IF NOT EXISTS idx_news_raw_published_at ON news_raw (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_raw_source_name   ON news_raw (source_name);