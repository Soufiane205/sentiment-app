"""API FastAPI pour l'analyse de sentiment."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.predict import predict

app = FastAPI(
    title="Sentiment API",
    description="Analyse de sentiment d'avis clients (positive / negative)",
    version="1.0.0",
)


class AvisRequest(BaseModel):
    texte: str


class AvisResponse(BaseModel):
    label: str
    score: float
    verdict: str


@app.get("/", summary="Santé de l'API")
def health():
    return {"status": "ok", "message": "Sentiment API opérationnelle"}


@app.post("/predict", response_model=AvisResponse, summary="Prédire le sentiment")
def predict_sentiment(body: AvisRequest):
    """Renvoie le label (positive/negative), le score de confiance et un verdict lisible."""
    try:
        result = predict(body.texte)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    verdict = "✅ Positif" if result["label"] == "positive" else "❌ Négatif"
    return AvisResponse(label=result["label"], score=result["score"], verdict=verdict)
