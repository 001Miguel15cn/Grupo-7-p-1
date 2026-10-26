"""Utilidades compartidas del Proyecto 2 y 3 (DIJIN 2025, Grupo 7).

ZANAHORIA_2026: este módulo concentra solo lo que se repite entre notebooks
(lectura de los xlsx crudos, panel municipio-mes, perfil por municipio).
Los pasos de limpieza con su justificación viven dentro de fase_b_limpieza.ipynb.
"""
from pathlib import Path

import numpy as np
import pandas as pd

# Orden natural de la edad de la víctima (variable ordinal)
ZANAHORIA_2026_ORDEN_EDAD = ["MENORES", "ADOLESCENTES", "ADULTOS"]

# Agrupación de los 8 tipos de delito en 4 familias (evita columnas casi vacías)
ZANAHORIA_2026_FAMILIA_DELITO = {
    "HURTO A PERSONAS": "HURTO",
    "HURTO A RESIDENCIAS": "HURTO",
    "HURTO PIRATERÍA TERRESTRE": "HURTO",
    "VIOLENCIA INTRAFAMILIAR": "VIF",
    "HOMICIDIO INTENCIONAL": "HOMICIDIO",
    "HOMICIDIOS EN ACCIDENTE DE TRÁNSITO": "HOMICIDIO",
    "SECUESTRO": "OTROS",
    "TERRORISMO": "OTROS",
}
ZANAHORIA_2026_FAMILIAS = ["HURTO", "VIF", "HOMICIDIO", "OTROS"]


def zanahoria_2026_raiz() -> Path:
    """ZANAHORIA_2026: devuelve la raíz del proyecto sin importar desde dónde corre el notebook."""
    actual = Path.cwd()
    return actual.parent if actual.name == "entrega" else actual


def zanahoria_2026_cargar_crudo(carpeta_datos: Path) -> pd.DataFrame:
    """ZANAHORIA_2026: lee los 8 .xlsx de la DIJIN y los apila en un solo DataFrame crudo.

    Cada archivo trae el encabezado real en la fila 11 (header=10) y no trae la
    columna de tipo de delito, que se deriva del nombre del archivo.
    """
    archivos = sorted(Path(carpeta_datos).glob("*.xlsx"))
    assert archivos, f"No se encontraron .xlsx en {Path(carpeta_datos).resolve()}"
    marcos = []
    for archivo in archivos:
        datos = pd.read_excel(archivo, header=10)
        datos.columns = [c.strip() for c in datos.columns]
        # dos archivos usan '*AGRUPA EDAD PERSONA*' en vez de 'AGRUPA_EDAD_PERSONA'
        datos = datos.rename(columns={"*AGRUPA EDAD PERSONA*": "AGRUPA_EDAD_PERSONA"})
        datos["TIPO_DELITO"] = archivo.stem.removesuffix("2025").strip().replace("_", " ").upper()
        marcos.append(datos)
    return pd.concat(marcos, ignore_index=True)


def zanahoria_2026_panel_mensual(df: pd.DataFrame) -> pd.DataFrame:
    """ZANAHORIA_2026: agrega los casos a un panel municipio x mes (12 meses, relleno con ceros).

    Espera un DataFrame de casos ya limpio con las columnas: dane, departamento,
    municipio, fecha, tipo_delito, arma_grupo, genero, edad (NaN permitido en
    genero/edad). Devuelve una fila por (dane, mes) con conteos y 'sumas de apoyo'
    para poder calcular porcentajes acumulados sin fuga de información.
    """
    c = df.copy()
    c["mes"] = c["fecha"].dt.month
    c["familia"] = c["tipo_delito"].map(ZANAHORIA_2026_FAMILIA_DELITO)
    c["fin_sem"] = (c["fecha"].dt.dayofweek >= 5).astype(int)
    c["tiene_genero"] = c["genero"].notna().astype(int)
    c["es_fem"] = (c["genero"] == "FEMENINO").astype(int)
    c["tiene_edad"] = c["edad"].notna().astype(int)
    c["edad_ord"] = c["edad"].map({k: i for i, k in enumerate(ZANAHORIA_2026_ORDEN_EDAD)})
    c["es_fuego"] = (c["arma_grupo"] == "ARMA DE FUEGO").astype(int)
    c["es_sin_arma"] = (c["arma_grupo"] == "SIN EMPLEO DE ARMAS").astype(int)
    for fam in ZANAHORIA_2026_FAMILIAS:
        c[f"casos_{fam.lower()}"] = (c["familia"] == fam).astype(int)

    agg = {
        "casos_hurto": "sum", "casos_vif": "sum", "casos_homicidio": "sum", "casos_otros": "sum",
        "fin_sem": "sum", "tiene_genero": "sum", "es_fem": "sum", "tiene_edad": "sum",
        "edad_ord": "sum", "es_fuego": "sum", "es_sin_arma": "sum",
    }
    g = c.groupby(["dane", "mes"]).agg(casos=("dane", "size"), dias_activos=("fecha", "nunique"), **{
        k: (k, v) for k, v in agg.items()})

    # rejilla completa: toda combinación municipio x mes; la ausencia de casos es un 0 real
    municipios = (c.groupby("dane")[["departamento", "municipio"]].first())
    rejilla = pd.MultiIndex.from_product([municipios.index, range(1, 13)], names=["dane", "mes"])
    g = g.reindex(rejilla)
    g = g.fillna(0).astype(int).reset_index()
    g = g.merge(municipios.reset_index(), on="dane", how="left")
    return g.sort_values(["dane", "mes"]).reset_index(drop=True)


def zanahoria_2026_agregar_porcentajes(p: pd.DataFrame, sufijo: str = "") -> pd.DataFrame:
    """ZANAHORIA_2026: calcula porcentajes a partir de las sumas de apoyo (NaN si el denominador es 0)."""
    out = pd.DataFrame(index=p.index)
    out[f"pct_fin_semana{sufijo}"] = p["fin_sem"] / p["casos"].replace(0, np.nan)
    out[f"pct_femenina{sufijo}"] = p["es_fem"] / p["tiene_genero"].replace(0, np.nan)
    out[f"edad_ordinal_media{sufijo}"] = p["edad_ord"] / p["tiene_edad"].replace(0, np.nan)
    out[f"pct_arma_fuego{sufijo}"] = p["es_fuego"] / p["casos"].replace(0, np.nan)
    out[f"pct_sin_armas{sufijo}"] = p["es_sin_arma"] / p["casos"].replace(0, np.nan)
    return out


def zanahoria_2026_perfil_municipios(panel: pd.DataFrame) -> pd.DataFrame:
    """ZANAHORIA_2026: perfil anual por municipio (una fila por código DANE) para el clustering."""
    sumas = ["casos", "casos_hurto", "casos_vif", "casos_homicidio", "casos_otros", "fin_sem",
             "tiene_genero", "es_fem", "tiene_edad", "edad_ord", "es_fuego", "es_sin_arma"]
    per = panel.groupby("dane")[sumas].sum()
    per["meses_con_casos"] = panel.groupby("dane")["casos"].apply(lambda s: (s > 0).sum())
    pct = zanahoria_2026_agregar_porcentajes(per)
    out = pd.concat([per[["casos", "casos_hurto", "casos_vif", "casos_homicidio", "casos_otros",
                          "meses_con_casos"]], pct], axis=1)
    for fam in ["hurto", "vif", "homicidio", "otros"]:
        out[f"share_{fam}"] = out[f"casos_{fam}"] / out["casos"]
    ref = panel.groupby("dane")[["departamento", "municipio"]].first()
    return ref.join(out).reset_index()
