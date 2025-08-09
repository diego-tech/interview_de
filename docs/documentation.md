# 📄 Documento de Diseño y Justificación Técnica — Proyecto `interview_de`

## 1. Visión General del Proyecto
**Objetivo**  
Describe en pocas frases qué problema resuelve tu sistema y el contexto de la prueba técnica.

**Arquitectura General**  
Explica brevemente el flujo de datos y las tecnologías clave.  
Ejemplo:
- API externa → Ingesta → Limpieza / Normalización → Inserción en BBDD → Consulta / Análisis.

---

## 2. Diseño a Alto Nivel
**Diagrama Arquitectónico**  
*(Puedes usar ASCII o un diagrama de draw.io / mermaid)*  
```text
  [NewsAPI] ---> [Ingesta Flask] ---> [Limpieza y Transformación] ---> [BBDD Supabase/PostgreSQL]
                                   \
                                    ---> [Airflow Orquestación]
```
**Motivación del diseño**

* Explica por qué has elegido este flujo.
* Ventajas frente a alternativas.

---

## 3. Diseño a Bajo Nivel

**Componentes Principales**

* `src/services` → Extracción, limpieza y filtrado.
* `src/repositories` → Conexión y operaciones en base de datos.
* `src/schemas` → Scripts SQL para inicializar la BBDD.
* DAG de Airflow → Definición de tareas y dependencias.

**Configuración**

* Uso del archivo `.env` y variables críticas:

  * Claves API
  * Credenciales de BBDD
  * Fernet Key y Secret Key

---

## 4. Decisiones Técnicas

| Decisión                   | Alternativas Consideradas              | Justificación                                  |
| -------------------------- | -------------------------------------- | ---------------------------------------------- |
| Flask para ingesta inicial | FastAPI, ejecución directa con Airflow | Sencillez y rapidez para pruebas locales       |
| PostgreSQL (Supabase)      | MySQL, SQLite                          | Entorno cloud gestionado, soporte SQL estándar |
| Modelo relacional          | NoSQL                                  | Integridad referencial y consultas complejas   |
| Airflow (CeleryExecutor)   | SequentialExecutor, cronjobs           | Escalabilidad y monitorización                 |
| Docker Compose             | Instalación manual                     | Portabilidad y reproducibilidad                |

---

## 5. Plan de Puesta en Producción

**Infraestructura**

* Airflow desplegado en Kubernetes / ECS
* PostgreSQL gestionado en la nube

**Logging y Monitorización**

* Logs de Airflow centralizados
* Alertas vía email o Slack

**Seguridad**

* Variables sensibles en gestor de secretos
* HTTPS en endpoints

**Estrategia de despliegue**

* Entorno de staging para pruebas
* Producción con DAGs programados y monitorizados

---

## 6. Escalabilidad y Evolución

* Posibilidad de añadir nuevas fuentes de datos
* Procesado batch o en streaming
* Integración con herramientas de BI

---

## 7. Conclusión

Resumen de por qué la solución es robusta, escalable y alineada con la prueba técnica.