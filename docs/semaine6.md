# Semaine 6 : le paquet, notes du binôme

## 1. Pourquoi le modèle n'est-il pas dans la roue ? Comment le paquet le trouve-t-il ?

La roue livre le code et ses dépendances déclarées. Le modèle entraîné a un cycle
de vie distinct : on peut le remplacer après un entraînement sans republier le code.
Les jeux de données, les tests et les fichiers `.joblib` sont donc exclus.

`sentiment_app.predict.chemin_modele()` lit `SENTIMENT_MODELE`. Sans cette variable,
le chemin par défaut est `models/sentiment.joblib`, à côté des sources dans le dépôt.
Dans une installation hors du dépôt, il faut fournir le modèle et définir la variable
avant de lancer la commande. Sans modèle, `sentiment predict` explique le problème
et renvoie le code 1. Le modèle est ensuite chargé une seule fois par processus.

## 2. Qu'est-ce qui a changé dans api/model.py quand predict() est entré dans le paquet ?

L'API n'ajoute plus `src/` à `sys.path`. Elle importe directement `charger_modele`
et `predict` depuis `sentiment_app.predict`. Ces imports fonctionnent aussi après
installation de la roue, où `src/` n'existe pas.

L'adaptateur `src/predict.py` garde les anciens scripts utilisables et fait pointer
`import predict` vers le même module que `sentiment_app.predict`. Cela conserve le
cache et permet aux anciens tests de modifier le chemin du modèle utilisé par l'API.
La commande `predict` passe par `api.model.load_model()` : elle applique donc aussi
le seuil d'abstention et les étiquettes du contrat de l'API.

## 3. Hors du dépôt : qu'a-t-il fallu fournir, et pourquoi scikit-learn est-il épinglé ?

Il faut installer la roue, laisser pip installer les dépendances déclarées et fournir
le fichier `sentiment.joblib` avec `SENTIMENT_MODELE`. Python 3.11 est utilisé pour
les vérifications du cours. L'interface nécessite l'option `[ui]` et une API démarrée.

Le modèle de ce projet a été entraîné avec scikit-learn 1.5.2. Le paquet impose
`>=1.5,<1.6`, et la CI installe ses dépendances depuis ce même paquet avant
l'entraînement. Cela évite de produire en CI un modèle avec une autre branche de
scikit-learn que celle utilisée pour le relire. Les modèles sérialisés ne sont pas
garantis compatibles entre versions : pour une reproduction exacte, conserver aussi
la version précise de l'environnement d'entraînement.

## Vérifications reproductibles

Depuis la racine du dépôt, avec le venv du projet :

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[ui]"
.\.venv\Scripts\python.exe -m pytest -q --cov=api --cov-report=term-missing --cov-fail-under=95
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy api
.\.venv\Scripts\python.exe -m build --wheel
.\.venv\Scripts\python.exe scripts/check_wheel.py dist/sentiment_app-0.6.0-py3-none-any.whl --model models/sentiment.joblib
```

`scripts/check_wheel.py` inspecte le contenu de la roue, crée un environnement neuf,
installe la roue et ses dépendances, vérifie la provenance des imports, puis exécute
la commande depuis un dossier temporaire. Il vérifie l'échec sans modèle, un avis
positif et l'abstention sur des mots inconnus. L'option `--reuse-dependencies` permet
un essai local sans téléchargement ; elle ne constitue pas une installation autonome
des dépendances. La CI utilise le mode normal.

Les résultats locaux sont consignés dans le journal du TP6 et dans
`docs/validation-tp6.txt`. Le commit de code `152705e` est publié sur `main`.
La livraison est versionnée `v0.6.0`. L'[exécution GitHub Actions du code](https://github.com/Soufiane205/sentiment-app/actions/runs/41877763496)
était en file d'attente au dernier contrôle, sans étape démarrée : son verdict
reste à confirmer. Le contrôle sur le poste du deuxième membre reste à réaliser.
