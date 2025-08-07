Aquí tienes un plan de trabajo y estructura de carpetas listos para que empieces de inmediato con la prueba técnica:

---

## 🗂 Estructura de carpetas

```plaintext
news-pipeline/
├── .env.example
├── README.md
├── DOCUMENTATION.md      ← Guía detallada y diseño de arquitectura
├── requirements.txt
├── docs/
│   └── architecture.png
├── storage/
│   ├── raw/
│   ├── processed/
│   └── dlq/
├── src/
│   ├── app/              ← Flask API
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── extract/
│   │   ├── newsapi_client.py
│   │   └── save_raw.py
│   ├── transform/
│   │   ├── cleaner.py
│   │   └── enrich.py
│   ├── load/
│   │   ├── models.py
│   │   └── loader.py
│   ├── common/
│   │   └── utils.py
│   └── pipeline.py       ← Orquestación básica (extract→transform→load)
├── dags/                 ← Airflow (opcional)
│   └── news_pipeline.py
├── infra/                ← IaC (opcional)
│   └── main.tf
└── tests/
    ├── app/
    │   └── test_routes.py
    ├── extract/
    │   └── test_newsapi_client.py
    ├── transform/
    │   └── test_cleaner.py
    └── load/
        └── test_loader.py
```

---

## 🚀 Plan de Trabajo y Cronograma

| Fase      | Objetivo                          | Tareas clave                                                                                                                                                    | Duración aprox. |
| --------- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 1         | **Preparación y extracción**      | - Crear entorno virtual, `.env` y dependencias<br>- Obtener API Key de News API<br>- Implementar `newsapi_client.py` + `save_raw.py` y probar fetch             | 4 h             |
| 2         | **Limpieza y transformación**     | - Definir reglas de filtrado (AI & Marketing en contenido)<br>- Escribir `cleaner.py` y `enrich.py`<br>- Validar con datos de prueba                            | 4 h             |
| 3         | **Modelado y carga**              | - Diseñar esquema SQL en `models.py`<br>- Desarrollar `loader.py` con batch inserts y ON CONFLICT<br>- Probar carga en local (Postgres/SQLite)                  | 3 h             |
| 4         | **Orquestación y monitorización** | - Crear `pipeline.py` para flujo síncrono<br>- Opcional: DAG en Airflow (`dags/news_pipeline.py`) con retries y DLQ<br>- Añadir logging JSON y métricas básicas | 4 h             |
| 5         | **API REST en Flask**             | - Scaffold de Flask en `src/app/`<br>- Endpoints `POST /run-pipeline` y `GET /articles`<br>- Tests con `pytest` en `tests/app`                                  | 3 h             |
| 6         | **Arquitectura y despliegue**     | - Dibujar diagrama (docs/architecture.png)<br>- Redactar sección “Despliegue” en DOCUMENTATION.md (Terraform/AWS/GCP)<br>- Probar infra local (opcional)        | 3 h             |
| 7         | **Documentación y presentación**  | - Completar `DOCUMENTATION.md` (flujo, DDL, ejemplos de requests/responses)<br>- Crear slides o PDF para presentación de 20 min                                 | 4 h             |
| **Total** |                                   |                                                                                                                                                                 | **25 h**        |

> Puedes ajustar la duración según tu disponibilidad; el objetivo es cubrir toda la prueba en 3–4 días de trabajo concentrado.

---

## 🎯 Siguientes Pasos Inmediatos

1. **Clonar y preparar el entorno**

   ```bash
   git clone <URL_DEL_REPO>
   cd news-pipeline
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env  # añade tu NEWSAPI_KEY, DATABASE_URL...
   ```

2. **Implementar y probar la extracción**

   * Abre `src/extract/newsapi_client.py`, coloca tu API key en `.env` y ejecuta un script de prueba para validar que recibes noticias.

3. **Avanzar por fases**

   * Una vez la extracción funcione, continúa con limpieza/transformación, y así sucesivamente según el plan.

---

Con este roadmap y estructura de carpetas, estarás listo para arrancar hoy mismo. ¡Éxito y avísame si necesitas ayuda en cualquiera de las fases!
