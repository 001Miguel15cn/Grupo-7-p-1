# Proyecto 2 y 3 — Análisis, limpieza y modelado · Estadísticas delictivas de Colombia 2025 (DIJIN)
Grupo 7 · Introducción a la ciencia de los datos · R.A. 2 y 3

**Pregunta de negocio:** ¿cuántos casos delictivos registrará cada municipio el mes siguiente?
Problema de **regresión** (3 modelos supervisados del mismo tipo + K-Means como modelo no supervisado).

## Estructura
```
entrega/
  fase_a_eda.ipynb          Fase A — análisis exploratorio
  fase_b_limpieza.ipynb     Fase B — limpieza y normalización
  fase_c_modelos.ipynb      Fase C — 3 modelos de regresión + K-Means
  datos_limpios.parquet     Salida de la Fase B (entrada de la Fase C)
  informe_p2p3.pdf          Informe final (Fase D)
  presentacion.pdf          Presentación oral
datos/                      8 reportes .xlsx originales de la DIJIN (+ perfil_municipios.parquet, generado por la Fase B)
figuras/                    Gráficos generados por los notebooks (no se versiona)
utilidades_delitos.py       Funciones compartidas (lectura de los xlsx, panel municipio-mes)
requirements.txt  .env.example  README.md
```

## Cómo correrlo
```bash
pip install -r requirements.txt
cd entrega
jupyter nbconvert --to notebook --execute --inplace fase_a_eda.ipynb
jupyter nbconvert --to notebook --execute --inplace fase_b_limpieza.ipynb   # genera datos_limpios.parquet
jupyter nbconvert --to notebook --execute --inplace fase_c_modelos.ipynb    # requiere la Fase B ya ejecutada
```
O abrir cada notebook y usar **Restart & Run All**, en el orden A → B → C. Tiempos aproximados: A ≈ 1 min,
B ≈ 1,5 min (lectura de los Excel), C ≈ 2 min. Semilla fija (`random_state=42`): los resultados son reproducibles en un mismo entorno;
con otras versiones de pandas o scikit-learn puede variar la tercera cifra decimal de algunas métricas
(el imputador KNN desempata vecinos de forma distinta), sin cambiar ninguna conclusión.

## Decisiones clave (detalle en los notebooks y el informe)
- Se agrega a un panel **municipio × mes** porque la fuente (un caso por fila) no tiene variables numéricas.
- Se **conservan** duplicados (son casos distintos) y atípicos (son las capitales); se controlan con `log1p` y `RobustScaler`.
- La partición 80/20 se hace **antes** de aprender medianas, vecinos KNN o escalas (sin data leakage).
- Los modelos predicen la variación sobre el mes anterior y se comparan contra la regla ingenua "este mes = el mes anterior".

---

## Cómo cambiar el proyecto para leer desde la bodega del Proyecto 1

Por defecto los notebooks leen los 8 `.xlsx` de `datos/` (el mismo dataset del Proyecto 1, sin pasar por la base de datos).
Para leer de la bodega (`hecho_delito` + 5 dimensiones) hay que tocar **un solo lugar de lectura** y ajustar dos detalles de limpieza.

> **Verificado:** se ejecutó `fase_b_etl.ipynb` del Proyecto 1 para reconstruir la bodega (SQLite) y se probó la consulta de abajo:
> devuelve 480.091 filas, con 1.477 nulos de género y 886 de edad (idénticos a los de la lectura de los xlsx) y 2 casos con municipio `NO REPORTADO`.

### 1. Credenciales y dependencias
- Los notebooks del Proyecto 1 usan `DATABASE_URL` del `.env` y, si no existe, SQLite en `datos/bodega_delitos.db`.
  Para este proyecto basta con dejar ese archivo en la carpeta `datos/` y no definir nada, o definir la URL de PostgreSQL.
- Copiar `.env.example` a `.env` y definir la misma `DATABASE_URL` del Proyecto 1, por ejemplo
  `DATABASE_URL=postgresql+psycopg2://usuario:clave@host:5432/bodega_delitos` (o `sqlite:///datos/bodega_delitos.db`).
- Agregar a `requirements.txt`: `sqlalchemy`, `python-dotenv` y, si es PostgreSQL, `psycopg2-binary`.

### 2. Reemplazar la lectura en `utilidades_delitos.py`
En vez de `cargar_datos_crudos(carpeta_datos)` (que lee los xlsx), usar una función que reconstruya **las mismas 9 columnas**
que esperan los notebooks (`ARMAS MEDIOS, DEPARTAMENTO, MUNICIPIO, FECHA HECHO, GENERO, AGRUPA_EDAD_PERSONA, CODIGO DANE, CANTIDAD, TIPO_DELITO`):

```python
import os
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

def cargar_datos_crudos_bodega(raiz) -> pd.DataFrame:
    """Reconstruye el consolidado de casos uniendo hecho_delito con sus 5 dimensiones."""
    load_dotenv(raiz / ".env")
    engine = create_engine(os.environ["DATABASE_URL"])
    consulta = """
        SELECT a.arma_medio  AS "ARMAS MEDIOS",  g.departamento AS "DEPARTAMENTO", g.municipio AS "MUNICIPIO",
               t.fecha       AS "FECHA HECHO",   v.genero       AS "GENERO",       v.grupo_edad AS "AGRUPA_EDAD_PERSONA",
               g.codigo_dane AS "CODIGO DANE",   h.cantidad     AS "CANTIDAD",     d.tipo_delito AS "TIPO_DELITO"
        FROM hecho_delito h
        JOIN dim_tiempo t       ON h.fecha_id  = t.fecha_id
        JOIN dim_geografia g    ON h.geo_id    = g.geo_id
        JOIN dim_tipo_delito d  ON h.delito_id = d.delito_id
        JOIN dim_arma_medio a   ON h.arma_id   = a.arma_id
        JOIN dim_victima v      ON h.victima_id = v.victima_id
    """
    df = pd.read_sql(consulta, engine)
    # Los notebooks esperan la fecha como texto dd/mm/aaaa
    df["FECHA HECHO"] = pd.to_datetime(df["FECHA HECHO"]).dt.strftime("%d/%m/%Y")
    # La bodega guardó los faltantes como "NO REPORTADO"; se devuelven a NaN para que la Fase B los trate
    df[["GENERO", "AGRUPA_EDAD_PERSONA"]] = df[["GENERO", "AGRUPA_EDAD_PERSONA"]].replace("NO REPORTADO", np.nan)
    return df
```

Luego, en `fase_a_eda.ipynb` y `fase_b_limpieza.ipynb`, cambiar la llamada
`cargar_datos_crudos(RAIZ / "datos")` por `cargar_datos_crudos_bodega(RAIZ)`.

### 3. Diferencias que van a notar (no son errores)
- **Pies de página:** la bodega ya los eliminó, así que el diagnóstico de la Fase B mostrará **0 filas de pie** (en vez de 40).
- **Conteos de nulos:** como el Proyecto 1 convirtió los nulos de género y edad en `NO REPORTADO`, el paso 2 reemplaza esas marcas por `NaN`
  para que la imputación por moda de la Fase B encuentre los mismos 1.168 y 577 nulos puntuales y los 309 estructurales.
- **Municipio sin nombre (2 casos de Nariño):** en la bodega aparecen como `NO REPORTADO` y no como nulo; la regla `SIN ESPECIFICAR (NARIÑO)` de la Fase B
  no se activa, pero el resultado es equivalente.
- **Armas raras:** la bodega conserva las 23 categorías; la Fase B sigue agrupando las de menos de 0,1 % en `OTRO`.
- **Validación:** la aserción de la Fase B (`480 091` casos) debe seguir cumpliéndose; si falla, la bodega y los xlsx no coinciden.
- Las demás celdas (panel, atípicos, partición, modelos, clustering) **no cambian**, porque trabajan sobre el mismo DataFrame de casos.
