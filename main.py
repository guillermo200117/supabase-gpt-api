from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import openai
import psycopg2
import os

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar API Key de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Ruta de prueba
@app.get("/")
def home():
    return {"status": "API funcionando correctamente"}

# Ruta para consultas en lenguaje natural
@app.post("/query")
async def consultar_datos(request: Request):
    data = await request.json()
    pregunta = data.get("consulta", "")

    if not pregunta:
        return {"error": "No se recibió una consulta válida"}

    # Pedir a OpenAI que genere una consulta SQL a partir de lenguaje natural
    prompt = f"""
    Eres un asistente experto en SQL. Genera una consulta SQL para PostgreSQL basada en esta pregunta:
    '{pregunta}'
    La tabla se llama "informe_eticos_x_linea" y tiene las siguientes columnas:
    fecha_reporte, linea, equipo, zona, representante, ruta, producto,
    presupuesto_unidades, presupuesto_valores,
    ventas_unidades, ventas_valores,
    cumplimiento_unidades, cumplimiento_valores.
    
    Devuelve solo la consulta SQL. No expliques nada.
    """

    try:
        respuesta_ai = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        sql_query = respuesta_ai.choices[0].message.content.strip()

        # Conectar a Supabase (PostgreSQL)
        conn = psycopg2.connect(
            host=os.getenv("SUPABASE_HOST"),
            database=os.getenv("SUPABASE_DB"),
            user=os.getenv("SUPABASE_USER"),
            password=os.getenv("SUPABASE_PASSWORD"),
            port="5432"
        )
        cur = conn.cursor()
        cur.execute(sql_query)
        filas = cur.fetchall()
        columnas = [desc[0] for desc in cur.description]
        resultados = [dict(zip(columnas, fila)) for fila in filas]
        cur.close()
        conn.close()

        return {"sql": sql_query, "resultados": resultados}
