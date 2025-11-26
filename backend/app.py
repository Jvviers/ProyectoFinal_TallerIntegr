from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import joblib
from preprocessing.pipeline import process_log_file

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# cargar el pipeline completo
model = joblib.load("model/model_pipeline.pkl")

# Mapeo de etiquetas numericas a actividades legibles
ACTIVITIES = {
    0: "Standing",
    1: "Jogging",
    2: "Running",
    3: "Walking",
    4: "Upstairs",
    5: "Downstairs",
    6: "Sitting",
    7: "Lying",
    8: "Cycling",
}


@app.get("/health")
def health():
    return {"status": "ok", "message": "backend listo"}


@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    try:
        raw = await file.read()
        df, info = process_log_file(raw)

        preds = model.predict(df)
        labels = [ACTIVITIES.get(int(p), f"Unknown ({p})") for p in preds]

        return {
            "prediction": preds.tolist(),
            "predicted_labels": labels,
            "samples": len(preds),
            "preprocessing": info,
            "status": "complete",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {e}")
