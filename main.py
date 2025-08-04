from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "API funcionando correctamente"}

@app.get("/ventas")
def obtener_ventas(
    zona: str = Query(None),
    ruta: str = Query(None),
    representante: str = Query(None),
    ano: str = Query(None),
    mes: str = Query(None),
):
    conn = psycopg2.connect(
        host="db.pxeltnnjywvtihbrlanr.supabase.co",
        database="postgres",
        user="postgres",
        password=os.getenv("SUPABASE_PASSWORD"),
        port="5432"
    )
    cur = conn.cursor()

    query = """
    SELECT 
        ano, mes, zona, ruta, representante, producto,
        SUM(presupuesto_unidades) AS presupuesto_unidades,
        SUM(presupuesto_valores) AS presupuesto_valores,
        SUM(ventas_unidades) AS ventas_unidades,
        SUM(ventas_valores) AS ventas_valores,
        ROUND(AVG(cumplimiento_unidades), 2) AS cumplimiento_unidades,
        ROUND(AVG(cumplimiento_valores), 2) AS cumplimiento_valores
    FROM "informe_eticos_x_linea"
    WHERE 1=1
    """

    if zona:
        query += f" AND zona = '{zona}'"
    if ruta:
        query += f" AND ruta = '{ruta}'"
    if representante:
        query += f" AND representante = '{representante}'"
    if ano:
        query += f" AND ano = '{ano}'"
    if mes:
        query += f" AND mes = '{mes}'"

    query += " GROUP BY ano, mes, zona, ruta, representante, producto"

    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    columnas = [
        "ano", "mes", "zona", "ruta", "representante", "producto",
        "presupuesto_unidades", "presupuesto_valores",
        "ventas_unidades", "ventas_valores",
        "cumplimiento_unidades", "cumplimiento_valores"
    ]

    resultados = [dict(zip(columnas, fila)) for fila in rows]
    return resultados
