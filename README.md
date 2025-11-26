# Proyecto Final – Reconocimiento de Actividad Humana (MHealth)

Aplicación web completa para cargar archivos `.log` del dataset MHealth y obtener la predicción del modelo entrenado.

## Estructura del proyecto
```
backend/
  app.py
  preprocessing/pipeline.py
  model/model_pipeline.pkl   # (ignorado en git)
  requirements.txt
  Dockerfile
frontend/
  index.html
  app.js
  styles.css
  Dockerfile
docker-compose.yml
prompts/
```

## Ejecutar con Docker
En la raíz del proyecto:
```bash
docker-compose up --build
```
- Frontend: http://localhost:8080  
- Backend (docs): http://localhost:8000/docs

## Endpoints principales
### GET /health
```json
{"status": "ok", "message": "backend listo"}
```

### POST /detect
Entrada: archivo `.log` en `form-data` con clave `file`.  
Salida (ejemplo):
```json
{
  "prediction": [1, 1, 2],
  "predicted_labels": ["Jogging", "Jogging", "Running"],
  "samples": 3,
  "preprocessing": {
    "separator": "\\t",
    "columns_detected": 24,
    "label_column": "Label"
  },
  "status": "complete"
}
```

#### Probar con curl
```bash
curl -X POST -F "file=@test_logs/subject1.log" http://localhost:8000/detect
```

## Validaciones del pipeline
- Detecta separador (`\t` o espacios).
- Detecta si la última columna es `Label` o `Subject` (enteros).
- Lanza error claro si hay más o menos columnas de las 23 de señales.
- Devuelve metadatos de preprocesamiento en la respuesta.

## Manejo de errores (400)
- Archivo vacío o no legible.
- Separador no detectado.
- Número de columnas diferente a 23 (+ opcional Label/Subject).

## Lista de actividades (mapa 0–8)
```
0: Standing
1: Jogging
2: Running
3: Walking
4: Upstairs
5: Downstairs
6: Sitting
7: Lying
8: Cycling
```

## Arquitectura (resumen)
```
[Frontend HTML/JS/Bootstrap] --HTTP--> [FastAPI /detect] --joblib--> [model_pipeline.pkl]
                                     \--> [preprocessing pipeline: limpieza/validación]
```

## Ejemplo rápido sin Docker
```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
# Abrir frontend/index.html en el navegador
```

## Notas de compatibilidad
- El modelo `model_pipeline.pkl` fue entrenado con scikit-learn 1.0.2; se fijan `scikit-learn==1.0.2`, `numpy==1.23.5` y `python-multipart` en `backend/requirements.txt`. Si cambias el modelo, usa la misma versión al entrenar para evitar errores de carga del pickle.

---
