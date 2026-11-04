# Journal des versions

## 0.6.0 — 2026-11-04 — TP6 : paquet installable

- Paquet `sentiment_app`, avec la version définie dans `sentiment_app/__init__.py`.
- Commande `sentiment --version`, `predict`, `serve` et `ui` ; lancement équivalent
  avec `python -m sentiment_app`.
- Prédiction déplacée dans `sentiment_app/predict.py` ; `src/predict.py` conserve
  les anciens imports et appels de scripts, y compris le cache et les modifications de `MODELE`.
- L'API importe le paquet sans modifier `sys.path` ; la commande applique le même
  seuil d'abstention de 0,60 que l'API.
- Modèle externe à la roue, configurable avec `SENTIMENT_MODELE`.
- Dépendances d'exécution déclarées dans `pyproject.toml`, avec scikit-learn
  `>=1.5,<1.6` ; dépendances Streamlit disponibles avec l'option `[ui]`.
- Roue contenant seulement `sentiment_app`, `api`, `ui` et les métadonnées.
- Tests du paquet et de la commande ; construction, installation hors du dépôt
  et conservation de la roue ajoutées à la CI.
- Corrections du chaînage des exceptions HTTP dans l'ancienne API `app/main.py`
  pour que la vérification Ruff du dépôt réussisse.

Les versions antérieures correspondent aux TP1 à TP5 ; ce fichier décrit la
livraison TP6 sans présumer de leur publication sous forme d'étiquettes Git.
