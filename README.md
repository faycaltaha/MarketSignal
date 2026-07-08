# MarketSignal — Anticipation des crises pour les entreprises

MarketSignal est un logiciel de prédiction qui aide les entreprises à **anticiper les crises**
(chocs de marché, retournements brutaux, régimes de forte volatilité) à partir de séries
temporelles de marché (prix d'actifs, indices, matières premières, taux de change…).

Il combine :

1. **Des indicateurs d'alerte précoce** — volatilité, drawdown, momentum, ratio de choc de
   volatilité, corrélation croisée entre actifs (les corrélations qui montent en flèche sont
   un signe classique de crise systémique).
2. **Un score de risque composite (0–100)** — agrégation pondérée et normalisée des
   indicateurs, avec des niveaux lisibles : `faible`, `modéré`, `élevé`, `critique`.
3. **Un modèle de machine learning** — régression logistique entraînée à prédire la
   probabilité d'un drawdown sévère dans les prochains jours (horizon et seuil configurables),
   validée par découpage temporel (pas de fuite de données du futur).
4. **Un moteur d'alertes** — règles métier qui produisent des messages actionnables en français.
5. **Une API REST + tableau de bord web** — pour intégrer le score dans vos outils ou le
   consulter dans un navigateur.
6. **Une CLI** — pour analyser un fichier CSV, entraîner le modèle et lancer le serveur.

## Installation

```bash
pip install -r requirements.txt
```

## Démarrage rapide

### 1. Générer un jeu de données de démonstration

```bash
python -m marketsignal demo --out data/demo_prices.csv
```

### 2. Analyser un fichier de prix

Le CSV doit contenir une colonne `date` et une colonne par actif (prix de clôture) :

```bash
python -m marketsignal analyze data/demo_prices.csv
```

Sortie : indicateurs courants, score de risque composite, niveau de risque, alertes actives
et probabilité de crise estimée par le modèle.

### 3. Entraîner et sauvegarder le modèle

```bash
python -m marketsignal train data/demo_prices.csv --model-out model.json
```

### 4. Lancer l'API et le tableau de bord

```bash
python -m marketsignal serve data/demo_prices.csv --port 8000
```

Puis ouvrir <http://localhost:8000/> pour le tableau de bord, ou consulter l'API :

| Endpoint            | Description                                        |
|---------------------|----------------------------------------------------|
| `GET /health`       | État du service                                    |
| `GET /risk/score`   | Score composite courant + niveau                   |
| `GET /risk/indicators` | Derniers indicateurs calculés                   |
| `GET /risk/alerts`  | Alertes actives                                    |
| `GET /risk/history?days=90` | Historique du score de risque              |
| `GET /predict`      | Probabilité de crise (modèle ML)                   |

## Format des données

```csv
date,actif_A,actif_B,actif_C
2024-01-02,100.0,50.2,201.3
2024-01-03,100.8,49.9,200.1
...
```

- `date` : ISO `YYYY-MM-DD`, une ligne par jour de cotation.
- Chaque autre colonne : prix de clôture d'un actif suivi par l'entreprise
  (indice sectoriel, matière première critique, devise d'exposition…).

## Comment la « crise » est-elle définie ?

Par défaut, une date est étiquetée *pré-crise* si, dans les **30 jours** suivants, le
portefeuille équipondéré subit un drawdown d'au moins **10 %**. Ces deux paramètres
(`horizon`, `seuil`) sont configurables dans la CLI et l'API. Le modèle apprend donc à
reconnaître les configurations de marché qui précèdent historiquement les chutes sévères.

## Tests

```bash
pytest
```

## Structure du projet

```
marketsignal/
├── data.py         # Chargement CSV + générateur de données synthétiques avec régimes de crise
├── indicators.py   # Indicateurs d'alerte précoce
├── scoring.py      # Score de risque composite 0–100
├── model.py        # Modèle ML de prédiction de crise (validation temporelle)
├── alerts.py       # Moteur d'alertes métier
├── api.py          # API FastAPI + tableau de bord HTML
└── cli.py          # Interface en ligne de commande
```

## Avertissement

MarketSignal est un outil d'aide à la décision : il fournit des probabilités et des signaux,
pas des certitudes. Il ne constitue pas un conseil financier.
