# Grupo 7 — Proyecto 1: Bodega de datos, ETL y Análisis Descriptivo

## Integrantes

| Integrante                 | Código de estudiante |
| -------------------------- | -------------------: |
| Juan David Quintero Garcia |              2559710 |
| Juan Jose Ospina           |              2559711 |
| Miguel Angel Arboleda      |              2160253 |
| Juan David Ascensio        |              2359660 |

**Dataset:** Estadísticas delictivas de Colombia 2025 — Policía Nacional, Dirección de Investigación Criminal e INTERPOL (DIJIN), Grupo de Información de Criminalidad.

## Cómo correr el proyecto

1. Clonar el repositorio e instalar dependencias:

   ```bash
   git clone <url-del-repo>
   cd grupo-7-p1
   pip install -r requirements.txt
   ```

2. Colocar los 8 archivos `.xlsx` originales del catálogo en `datos/`.

3. Para el uso local recomendado, no hace falta instalar ni iniciar un servidor de base de datos ni crear un `.env`. Si `DATABASE_URL` no está definida, los notebooks usan SQLite en `datos/bodega_delitos.db`.

4. Abrir y ejecutar los notebooks desde `entrega/`, en este orden y con **Restart & Run All**:

   * `entrega/fase_b_etl.ipynb` — construye y carga la bodega.
   * `entrega/fase_c_sql.ipynb` — 6 consultas analíticas.
   * `entrega/fase_d_visualizaciones.ipynb` — 8 visualizaciones con insights.

   La Fase B crea la base SQLite y también genera `datos/delitos_2025_consolidado.csv`; las fases C y D consultan esa misma base.

5. La configuración local es opcional. Si quieres declararla explícitamente, crea `.env` en la raíz del proyecto con:

   ```env
   DATABASE_URL=sqlite:///../datos/bodega_delitos.db
   ```

   Esa ruta relativa está pensada para ejecutar los notebooks desde `entrega/`.

6. Para usar PostgreSQL en vez de SQLite, cambia `DATABASE_URL` en `.env` por una URL como:

   ```env
   postgresql+psycopg2://usuario:clave@host:5432/bodega_delitos
   ```

   y asegúrate de que la base exista y el servidor esté disponible.

## Estructura

```text
grupo-7-p1/

├── entrega/
│   ├── fase_a_diseño.pdf
│   ├── fase_b_etl.ipynb
│   ├── fase_c_sql.ipynb
│   ├── fase_d_visualizaciones.ipynb
│   ├── informe.pdf
│   └── diagrama_bodega.png
├── datos/
├── .env.example
├── requirements.txt
└── README.md
```

La Fase B genera `datos/bodega_delitos.db` y `datos/delitos_2025_consolidado.csv` al ejecutarse.

## Modelo de datos

Modelo estrella: 1 tabla de hechos (`hecho_delito`, grano = un caso delictivo registrado) y 5 dimensiones (`dim_tiempo`, `dim_geografia`, `dim_tipo_delito`, `dim_arma_medio`, `dim_victima`).

Ver `entrega/fase_a_diseño.pdf` para el detalle y la justificación completa.