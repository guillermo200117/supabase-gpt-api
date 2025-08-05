from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import openai
import psycopg2

app = FastAPI()

# Configurar CORS para permitir el acceso desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta principal para verificar si la API está funcionando
@app.get("/")
def health_check():
    return {"status": "API funcionando correctamente"}

# Ruta para recibir preguntas en lenguaje natural y consultar Supabase
@app.post("/query")
async def consultar_datos(request: Request):
    try:
        data = await request.json()
        pregunta = data.get("consulta", "")

        # Conectar a la base de datos Supabase
        conn = psycopg2.connect(
            host=os.getenv("SUPABASE_HOST"),
            database=os.getenv("SUPABASE_DB"),
            user=os.getenv("SUPABASE_USER"),
            password=os.getenv("SUPABASE_PASSWORD"),
            port="5432"
        )
        cur = conn.cursor()

        # Enviar la pregunta al modelo de OpenAI
        prompt = f"""
Eres un experto en análisis de datos. Tengo una base de datos con la siguiente estructura:

(fecha_reporte, línea, equipo, zona, representante, ruta, producto, presupuesto_unidades, presupuesto_valores, ventas_unidades, ventas_valores, cumplimiento_unidades, cumplimiento_valores)

Con base en esto, genera una consulta SQL que responda a lo siguiente:
{pregunta}
"""

        respuesta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un asistente que genera consultas SQL para bases de datos PostgreSQL."},
                {"role": "user", "content": prompt}
            ]
        )

        sql_query = respuesta['choices'][0]['message']['content'].strip().strip("```sql").strip("```")

        cur.execute(sql_query)
        rows = cur.fetchall()
        columnas = [desc[0] for desc in cur.description]
        resultados = [dict(zip(columnas, fila)) for fila in rows]

        cur.close()
        conn.close()

        return {"sql": sql_query, "resultados": resultados}

    except Exception as e:
        return {"error": str(e)}
