# Orquestación y Pipeline ETL – Prueba Técnica

## 1. Requisitos previos

Para poder ejecutar el proyecto en local, se necesita:

* **Docker** y **Docker Compose** instalados. https://www.docker.com/products/docker-desktop/
* Cuentas y credenciales en:

  * **Supabase** (Base de datos PostgreSQL). https://supabase.com/
  * **NewsAPI** (para obtener la API Key).http://newsapi.org/
* Generar las claves necesarias:

  * **Fernet Key**: clave requerida por Apache Airflow para el cifrado de datos sensibles.

    ```bash
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    ```
  * **Secret Key**: clave interna para la comunicación y seguridad entre servicios Docker.

    ```bash
    python -c "import secrets; print(secrets.token_urlsafe(64))"
    ```

---

## 2. Configuración del archivo `.env`

En el repositorio existe un archivo `.env.example`.
Debes duplicarlo y renombrarlo como `.env` en la raíz del proyecto.

Ejemplo de variables necesarias:

```env
NEWSAPI_KEY=                # API Key generada en https://newsapi.org/
API_URL=https://newsapi.org/v2/everything
DATABASE_URL=               # Cadena de conexión completa a PostgreSQL en Supabase
DB_HOST=                    # Host de Supabase
DB_PORT=                    # Puerto de Supabase
DB_USER=                    # Usuario de la base de datos
DEBUG=                      # 1 o 0 – habilitar/deshabilitar modo debug en Flask
ENABLE_SCHEDULER=           # 1 o 0 – habilitar/deshabilitar APSCheduler en local
AIRFLOW_UID=50000           # UID por defecto para Apache Airflow
AIRFLOW__CORE__FERNET_KEY=  # Fernet Key generada previamente
AIRFLOW__WEBSERVER__SECRET_KEY= # Secret Key generada previamente
```

---

## 3. Configuración de la base de datos en Supabase

Este proyecto requiere una base de datos PostgreSQL en Supabase.
En el directorio `src/schemas` encontrarás dos archivos `.sql` con:

* Estructura de las tablas necesarias.
* Datos iniciales para el funcionamiento del pipeline.

Debes ejecutar ambos en tu instancia de Supabase antes de iniciar el pipeline.

---

## 4. Puesta en marcha del entorno

En la raíz del proyecto se encuentra el script:

```bash
./init.sh
```

Este script:

1. Construye y levanta los contenedores Docker (Airflow y dependencias).
2. Configura la orquestación a través de `docker/docker-compose.yml`.

Valores por defecto de acceso a la UI de Airflow:

* URL: [http://localhost:8080](http://localhost:8080)
* Usuario: **admin**
* Contraseña: **admin**

> ⚠ **Nota:** Usuario y contraseña son solo de ejemplo. Para producción deben reemplazarse por credenciales seguras.

---

## 5. Ejecución del Pipeline

El DAG `news_ai_marketing_ingestion` está programado para ejecutarse automáticamente **cada día a las 07:00** con los parámetros por defecto:

* `days_back = 7`
* `page_size = 100`
* `max_pages = 1`

> Actualmente solo se consulta **1 página**, debido a la limitación del plan gratuito de NewsAPI.

### Ejecución manual

1. Inicia sesión en Airflow ([http://localhost:8080](http://localhost:8080)).
2. Busca el DAG `news_ai_marketing_ingestion` en el panel principal.
3. Haz clic en el nombre para entrar en la vista de detalle.
4. Pulsa el botón **Run** (esquina superior derecha) para lanzarlo manualmente y seguir el proceso en tiempo real.