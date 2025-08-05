from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import openai
import psycopg2

# Inicializar FastAPI
app = FastAPI()

# Permitir solicitudes desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexión a la base de datos Supabase
SUPABASE_CONFIG = {
    "host": "db.pxeltnnjywvtihbrlanr.supabase.co",
    "database": "postgres",
    "user": "postgres",
    "password": os.getenv("SUPABASE_PASSWORD"),
    "port": "5432"
}

# Configurar clave de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.get("/")
def health_check():
    return {"status": "API funcionando correctamente"}

@app.post("/query")
async def consultar_datos(request: Request):
    data = await request.json()
    pregunta = data.get("consulta", "")

    # Instrucción para que GPT actúe como generador de SQL
    prompt = f"""
    Eres un experto en bases de datos PostgreSQL.
    Tu tarea es convertir preguntas en lenguaje natural en consultas SQL para la siguiente tabla:

    Tabla: informe_eticos_x_linea
    Columnas:
    - fecha_reporte
    - linea
    - equipo
    - zona
    - representante
    - ruta
    - producto
    - presupuesto_unidades
    - presupuesto_valores
    - ventas_unidades
    - ventas_valores
    - cumplimiento_unidades
    - cumplimiento_valores

    Solo genera la consulta SQL, sin explicaciones.

    Pregunta: {pregunta}
    SQL:
    """

    # Obtener la consulta SQL generada por GPT
    try:
        respuesta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente que convierte lenguaje natural en SQL."},
                {"role": "user", "content": prompt}
            ]
        )
        sql_generado = respuesta.choices[0].message.content.strip().strip("`")
    except Exception as e:
        return {"error": "Error al generar SQL con OpenAI", "detalle": str(e)}

    # Conectar a Supabase y ejecutar la consulta
    try:
        conn = psycopg2.connect(**SUPABASE_CONFIG)
        cur = conn.cursor()
        cur.execute(sql_generado)
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        resultados = [dict(zip(colnames, row)) for row in rows]
        cur.close()
        conn.close()
    except Exception as e:
        return {
            "sql": sql_generado,
            "error": "Error al ejecutar consulta SQL",
            "detalle": str(e)
        }

    return {
        "sql": sql_generado,
        "resultados": resultados
    }
