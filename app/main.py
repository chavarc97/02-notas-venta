import os
import time
import asyncio
import boto3
import fastapi
from fastapi import Request
from app.routes import notas
from app.db import engine, Base
from app.models import nota

Base.metadata.create_all(bind=engine)

app = fastapi.FastAPI(title="Microservicio - Notas de Venta")

# Extraemos el ambiente de las variables de entorno (por defecto 'local')
ENVIRONMENT = os.environ.get("ENVIRONMENT", "local")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

cloudwatch = boto3.client('cloudwatch', region_name=AWS_REGION)
NAMESPACE = "ExamenCloud/NotasVenta"

def push_metrics_to_cloudwatch(endpoint: str, method: str, status_code: int, process_time: float):
    """Envía métricas a AWS CloudWatch"""
    try:
        # Clasificar status code
        status_class = f"{str(status_code)[0]}XX"
        
        cloudwatch.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=[
                {
                    'MetricName': 'HttpRequestCount',
                    'Dimensions': [
                        {'Name': 'Environment', 'Value': ENVIRONMENT},
                        {'Name': 'Endpoint', 'Value': endpoint},
                        {'Name': 'StatusClass', 'Value': status_class}
                    ],
                    'Value': 1,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'HttpRequestDuration',
                    'Dimensions': [
                        {'Name': 'Environment', 'Value': ENVIRONMENT},
                        {'Name': 'Endpoint', 'Value': endpoint}
                    ],
                    'Value': process_time * 1000, # milisegundos
                    'Unit': 'Milliseconds'
                }
            ]
        )
    except Exception as e:
        # En producción deberíamos loggear esto correctamente
        print(f"Error enviando métricas a CloudWatch: {e}")

@app.middleware("http")
async def cloudwatch_metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Procesar la petición
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        raise e
    finally:
        process_time = time.time() - start_time
        
        # Ignorar peticiones a la ruta raíz si hace mucho ruido, pero aquí las mediremos todas.
        if request.url.path != "/favicon.ico":
            # Usar asyncio.to_thread para no bloquear el Event Loop de FastAPI con la llamada de boto3
            asyncio.create_task(
                asyncio.to_thread(
                    push_metrics_to_cloudwatch,
                    request.url.path,
                    request.method,
                    status_code,
                    process_time
                )
            )
            
    return response

app.include_router(notas.router)

@app.get("/")
def root():
    return {
        "message": "API Notas de Venta Funcional. Visita /docs para ver los endpoints interactivos."
    }
