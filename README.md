# sentiment-app : dépôt du binôme

Application fil rouge du cours *Développement et déploiement d'applications intelligentes* (A. Larhlimi).
Le besoin : une équipe relation client reçoit des milliers d'avis par jour et veut voir les **avis négatifs** en
tête de file. Le dépôt grandit chaque semaine ; rien n'est jeté.

| TP | Ce que le dépôt contient | Où | Compte rendu |
| --- | --- | --- | --- |
| TP1 | Environnement, structure, trois fiches de cadrage | `docs/cadrage/`, `scripts/` | les fiches |
| TP2 | Modèle TF-IDF et régression logistique, évaluation, métriques versionnées | `src/`, `models/metrics.json` | `docs/semaine2.md` |
| TP3 | API FastAPI : `GET /health`, `POST /predict` | `api/` | `docs/semaine3.md` |
| TP4 | Tests aux limites et d'intégration, abstention `INDETERMINE`, jeu d'or, ruff, mypy, pre-commit | `tests/`, `data/jeu_or.csv` | `docs/semaine4.md` |
| TP5 | Interface Streamlit, cliente de l'API | `ui/` | `docs/semaine5.md` |
| TP6 | Paquet installable et commande `sentiment` | `sentiment_app/`, `dist/` | `docs/semaine6.md` |

Le paquet est en version `0.6.0`. Les résultats des contrôles locaux du TP6 sont
consignés dans `docs/validation-tp6.txt`. La CI vérifie aussi la roue hors du dépôt ;
son résultat distant se consulte dans GitHub Actions après le push.

## Installation

Python 3.11 (3.12 et 3.13 sont à éviter : pas de versions précompilées pour certains paquets).

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1          # Linux, macOS, Git Bash : source .venv/bin/activate
python -m pip install -e ".[ui]" "pytest==8.3.*" -r requirements-dev.txt
pre-commit install                  # une fois par clone : ruff et mypy à chaque commit
python scripts/check_setup.py       # attendu : 0 erreur(s), 0 avertissement(s)
```

Cette installation reprend celle de la CI et fixe scikit-learn à la branche 1.5
avant l'entraînement. `requirements.txt` contient aussi les outils des semaines
suivantes ; ils ne sont pas nécessaires pour exécuter le paquet TP6.

## Installer ou reconstruire la roue (TP6)

Une roue `.whl` s'installe avec Python et crée la commande `sentiment`.
Depuis la racine du dépôt, utilisez explicitement le venv Python 3.11 pour éviter
une installation dans l'environnement Anaconda `(base)` :

```powershell
.\.venv\Scripts\python.exe -m pip install ".\dist\sentiment_app-0.6.0-py3-none-any.whl[ui]"
.\.venv\Scripts\sentiment.exe --version
$env:SENTIMENT_MODELE = (Resolve-Path .\models\sentiment.joblib).Path
.\.venv\Scripts\sentiment.exe predict "Livraison rapide, produit conforme, très satisfait"
.\.venv\Scripts\sentiment.exe serve # terminal 1 : API sur le port 8000
.\.venv\Scripts\sentiment.exe ui    # terminal 2 : interface sur le port 8501
```

L'option `[ui]` installe aussi Streamlit et les dépendances de l'interface.
Pour utiliser seulement `predict` et `serve`, installez la roue sans `[ui]`.
Le modèle reste séparé du paquet : sur un autre poste, copiez aussi
`models/sentiment.joblib` et indiquez son chemin dans `SENTIMENT_MODELE`, dans
chaque terminal qui exécute `predict` ou `serve`. Sans modèle existant, entraînez-le
avec les commandes de la section suivante.

Pour reconstruire et vérifier la roue (outils de développement installés) :

```powershell
.\.venv\Scripts\python.exe -m build --wheel
.\.venv\Scripts\python.exe scripts/check_wheel.py dist/sentiment_app-0.6.0-py3-none-any.whl --model models/sentiment.joblib
```

Seuls les paquets `sentiment_app`, `api` et `ui` sont inclus ; les tests, données et
modèles restent dans le dépôt. La roue impose scikit-learn 1.5 pour relire le modèle
produit par ce projet.

## Entraîner le modèle

Le modèle (`models/sentiment.joblib`) n'est jamais commité : il se reconstruit en une commande.

```powershell
python src/make_demo.py             # 290 avis de démonstration, 145 par classe
python src/train.py                 # F1 macro 0,879 sur le jeu de démonstration (seuil 0,85)
python src/evaluate.py              # matrice de confusion et exemples d'erreurs
python src/train.py --allocine      # facultatif : 20 000 avis Allociné, F1 macro 0,920
```

L'API, les tests et la CI utilisent le modèle du jeu de démonstration : après un entraînement sur Allociné,
relancez `python src/train.py`.

## Lancer l'application

Deux programmes tournent en même temps, chacun dans son terminal, environnement virtuel activé.

```powershell
uvicorn api.main:app --reload       # l'API : http://localhost:8000/docs
streamlit run ui/app.py             # la page : http://localhost:8501
```

L'API refuse de démarrer sans modèle. Si le port 8000 est déjà pris, lancez l'API avec `--port 8001` et
indiquez-le à la page : `$env:API_URL = "http://127.0.0.1:8001"` avant `streamlit run`.

Ce que l'API renvoie :

| Requête | Réponse |
| --- | --- |
| `{"text": "Livraison rapide, produit conforme, très satisfait"}` | 200, `POSITIVE`, 0,777 |
| `{"text": "Produit cassé et service injoignable, à fuir"}` | 200, `NEGATIVE`, 0,7465 |
| `{"text": "xqzvb wlkptr grombu"}` | 200, `INDETERMINE`, 0,5162 (confiance sous le seuil de 0,60) |
| `{"text": ""}`, `{"text": "   "}`, `{}`, `{"text": 42}` | 422, `detail` sous la forme standard de FastAPI |
| modèle retiré ou en panne | 503 ou 500, sans message interne |

## Tests et qualité

```powershell
python -m pytest -q
python -m pytest -q --cov=api --cov-report=term-missing --cov-fail-under=95
ruff check .
mypy api
python src/courbe_seuil.py          # compromis du seuil d'abstention
python src/bilan_jeu_or.py          # le jeu d'or : 10 justes, 9 abstentions, 1 erreur déclarée
```

Le `xfailed` est une erreur connue et déclarée du jeu d'or : une négation (« Je ne suis pas satisfait »)
que le sac de mots ne voit pas. Sans modèle sur le poste, les tests qui l'appellent sont ignorés.

| Fichier de tests | Ce qu'il vérifie |
| --- | --- |
| `test_environment.py`, `test_cadrage.py`, `test_git_history.py` | TP1 : environnement, fiches, deux auteurs de commits |
| `test_model.py` | TP2 : métriques versionnées, seuil de F1, `predict()` |
| `test_api.py` | TP3 : les réponses de l'API |
| `test_limites.py`, `test_integration.py`, `test_jeu_or.py` | TP4 : frontières du contrat, propriétés hypothesis, démarrage et pannes, jeu d'or |
| `test_client.py`, `test_interface.py` | TP5 : le client de l'API et la page Streamlit |
| `test_packaging.py`, `test_commande_sentiment.py` | TP6 : métadonnées, imports, modèle configurable et sous-commandes |

La CI (`.github/workflows/ci.yml`) rejoue à chaque push, sur une machine neuve : diagnostic, entraînement du
modèle de démonstration avec scikit-learn 1.5, ruff, mypy, tests avec un seuil de
couverture de 95 %, construction et installation de la roue hors du dépôt. La roue
est conservée dans l'artefact `sentiment-app-wheel`.

## Structure

```text
sentiment-app/
├── README.md, TESTS.md, AIDE-GIT.md, DEPANNAGE.md, MARCHE-A-SUIVRE*.md, TP*-ENONCE.md
├── requirements.txt, requirements-dev.txt, pyproject.toml, pytest.ini, .pre-commit-config.yaml
├── .github/workflows/ci.yml   # intégration continue
├── src/                       # TP2 : make_demo, train, evaluate, predict ; TP4 : courbe_seuil, bilan_jeu_or
├── api/                       # TP3 : main (routes), schemas (contrat Pydantic), model (seuil, étiquettes)
├── ui/                        # TP5 : app (la page), client (les appels à l'API)
├── sentiment_app/             # TP6 : version, prédiction et commande
├── dist/                      # roue générée, non suivie par Git
├── tests/                     # pytest, TP1 à TP6
├── data/                      # sample_reviews.csv, jeu_or.csv, avis_exemple.csv ; le reste est régénérable
├── models/                    # metrics.json seulement : le modèle n'est jamais commité
├── docs/                      # cadrage/ (fiches du TP1), semaine2.md à semaine6.md
├── scripts/                   # setup, diagnostic, création de fiche, clone de vérification
├── notebooks/                 # variantes Colab
└── exemples/                  # scripts d'aperçu fournis avec le TP1, non notés
```

Le dossier `app/` contient une ancienne API de démonstration. La commande `sentiment serve`
utilise l'API du cours dans `api/`.

## Membres du binôme

| Rôle | Nom | Identifiant GitHub | Travail de la semaine 1 |
| --- | --- | --- | --- |
| Membre A | Taha Tahir | Tahatahir-IIR | |
| Membre B | KHALDOUN Soufiane | Soufiane205 | |
