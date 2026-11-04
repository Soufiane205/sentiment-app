"""Tests d'intégration : l'API telle qu'elle tourne vraiment (TP4, étape D).

Les tests du TP3 vérifient des réponses ; ceux-ci vérifient le démarrage de l'API
et son comportement quand le modèle manque ou tombe en panne.
"""
from pathlib import Path

import pytest

MODELE = Path(__file__).resolve().parents[1] / "models" / "sentiment.joblib"
pytestmark = pytest.mark.skipif(not MODELE.exists(), reason="modèle non produit : python src/train.py")


@pytest.fixture
def cache_vide():
    """Vide le cache de chargement avant et après le test : aucun état ne survit d'un test à l'autre."""
    from predict import charger_modele

    charger_modele.cache_clear()
    yield
    charger_modele.cache_clear()


class ModeleEnPanne:
    """Remplace le modèle chargé : chaque prédiction lève l'exception donnée."""

    model_name = "modèle en panne (test)"

    def __init__(self, erreur: Exception) -> None:
        self.erreur = erreur

    def predict(self, text: str) -> dict:
        raise self.erreur


def test_demarrage_reel_charge_le_modele():
    """D.1 : un client ouvert par « with » exécute le lifespan."""
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app) as client:
        reponse = client.get("/health")
    assert reponse.status_code == 200
    assert "TP2" in reponse.json()["model"]


def test_modele_absent_l_api_refuse_de_demarrer(monkeypatch, tmp_path, cache_vide):
    """D.2 : le contrôle T20 du TP3, devenu automatique."""
    from fastapi.testclient import TestClient

    import predict
    from api.main import app

    monkeypatch.setattr(predict, "MODELE", tmp_path / "absent.joblib")
    with pytest.raises(FileNotFoundError, match="modèle introuvable"):
        with TestClient(app):
            pass


def test_modele_non_charge_503(monkeypatch):
    """D.3 : l'API démarrée, le modèle disparaît de app.state."""
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app) as client:
        monkeypatch.setattr(app.state, "classifier", None)
        assert client.get("/health").status_code == 503
        reponse = client.post("/predict", json={"text": "Livraison rapide"})
    assert reponse.status_code == 503
    assert reponse.json()["detail"] == "Modèle non chargé"


@pytest.mark.parametrize(
    "erreur",
    [RuntimeError("bug interne"), ValueError("bug interne")],
    ids=["RuntimeError", "ValueError"],
)
def test_modele_en_panne_500_sans_message_interne(monkeypatch, erreur):
    """D.4 : quelle que soit l'exception, 500, et le message interne ne sort pas de l'API."""
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app) as client:
        monkeypatch.setattr(app.state, "classifier", ModeleEnPanne(erreur))
        reponse = client.post("/predict", json={"text": "Livraison rapide"})
    assert reponse.status_code == 500
    assert "bug interne" not in reponse.text
    assert reponse.json()["detail"] == "Erreur interne du serveur"


def test_classes_inattendues_l_api_refuse_de_demarrer(monkeypatch):
    """E.3 : un modèle aux étiquettes hors contrat ne doit jamais être servi."""
    from fastapi.testclient import TestClient

    import api.model
    from api.main import app

    class ModeleTroisClasses:
        classes_ = ["negative", "neutre", "positive"]

    monkeypatch.setattr(api.model, "charger_modele", lambda: ModeleTroisClasses())
    with pytest.raises(ValueError, match="classes inattendues"):
        with TestClient(app):
            pass
