-- Extensión útil para búsquedas/filtros opcionales
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS news_keywords (
  id           BIGSERIAL PRIMARY KEY,
  term         TEXT        NOT NULL,
  category     TEXT        NOT NULL CHECK (category IN ('AI','MARKETING')),
  lang         TEXT        NOT NULL CHECK (char_length(lang)=2), -- 'es','en',...
  must_include BOOLEAN     NOT NULL DEFAULT TRUE,   -- si FALSE, se usará como sinónimo "suave" (suele ser TRUE)
  negate       BOOLEAN     NOT NULL DEFAULT FALSE,  -- si TRUE se antepone con NOT / '-' en la query
  active       BOOLEAN     NOT NULL DEFAULT TRUE,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(term, lang)
);

-- Índices útiles
CREATE INDEX IF NOT EXISTS idx_news_keywords_cat_lang ON news_keywords(category, lang) WHERE active;
CREATE INDEX IF NOT EXISTS idx_news_keywords_term_trgm ON news_keywords USING GIN (term gin_trgm_ops);

-- IA / ES
INSERT INTO news_keywords (term, category, lang) VALUES
('IA', 'AI', 'es'),
('inteligencia artificial', 'AI', 'es'),
('machine learning', 'AI', 'es'),
('aprendizaje automático', 'AI', 'es'),
('deep learning', 'AI', 'es'),
('redes neuronales', 'AI', 'es'),
('modelo de lenguaje', 'AI', 'es'),
('LLM', 'AI', 'es'),
('IA generativa', 'AI', 'es'),
('ChatGPT', 'AI', 'es')
ON CONFLICT (term, lang) DO NOTHING;

-- IA / EN
INSERT INTO news_keywords (term, category, lang) VALUES
('AI', 'AI', 'en'),
('artificial intelligence', 'AI', 'en'),
('machine learning', 'AI', 'en'),
('deep learning', 'AI', 'en'),
('neural networks', 'AI', 'en'),
('large language model', 'AI', 'en'),
('LLM', 'AI', 'en'),
('generative AI', 'AI', 'en'),
('ChatGPT', 'AI', 'en')
ON CONFLICT (term, lang) DO NOTHING;

-- MARKETING / ES
INSERT INTO news_keywords (term, category, lang) VALUES
('marketing', 'MARKETING', 'es'),
('marketing digital', 'MARKETING', 'es'),
('marketing de contenidos', 'MARKETING', 'es'),
('automatización de marketing', 'MARKETING', 'es'),
('growth marketing', 'MARKETING', 'es'),
('growth hacking', 'MARKETING', 'es'),
('redes sociales', 'MARKETING', 'es'),
('marketing en redes sociales', 'MARKETING', 'es'),
('SEO', 'MARKETING', 'es'),
('SEM', 'MARKETING', 'es'),
('email marketing', 'MARKETING', 'es')
ON CONFLICT (term, lang) DO NOTHING;

-- MARKETING / EN
INSERT INTO news_keywords (term, category, lang) VALUES
('marketing', 'MARKETING', 'en'),
('digital marketing', 'MARKETING', 'en'),
('content marketing', 'MARKETING', 'en'),
('marketing automation', 'MARKETING', 'en'),
('growth marketing', 'MARKETING', 'en'),
('growth hacking', 'MARKETING', 'en'),
('social media', 'MARKETING', 'en'),
('social media marketing', 'MARKETING', 'en'),
('SEO', 'MARKETING', 'en'),
('SEM', 'MARKETING', 'en'),
('email marketing', 'MARKETING', 'en')
ON CONFLICT (term, lang) DO NOTHING;