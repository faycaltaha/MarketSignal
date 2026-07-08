# MarketSignal — Anticipation des crises pour les entreprises

MarketSignal est un logiciel de prédiction qui aide les entreprises à **anticiper les crises**
(chocs de marché, retournements brutaux, régimes de forte volatilité) à partir de séries
temporelles de marché (prix d'actifs, indices, matières premières, taux de change…).

Il combine :

1. **Des indicateurs d'alerte précoce** — volatilité, drawdown, momentum, ratio de choc de
   volatilité, corrélation croisée entre actifs (les corrélations qui montent en flèche sont
   un signe classique de crise systémique).
2. **Des signaux faibles issus de la recherche académique** — turbulence statistique,
   ratio d'absorption, corrélations asymétriques baissières, réseau de causalité de
   Granger et relations avance/retard (voir la section « Signaux faibles » ci-dessous).
3. **Un score de risque composite (0–100)** — agrégation pondérée et normalisée des
   indicateurs, avec des niveaux lisibles : `faible`, `modéré`, `élevé`, `critique`.
4. **Un modèle de machine learning** — régression logistique entraînée à prédire la
   probabilité d'un drawdown sévère dans les prochains jours (horizon et seuil configurables),
   validée par découpage temporel (pas de fuite de données du futur).
5. **Un moteur d'alertes** — règles métier qui produisent des messages actionnables en français.
6. **Une API REST + tableau de bord web** — pour intégrer le score dans vos outils ou le
   consulter dans un navigateur.
7. **Une CLI** — pour analyser un fichier CSV, entraîner le modèle et lancer le serveur.

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
| `GET /risk/lead-lag` | Relations avance/retard entre séries (signaux faibles) |
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

## Signaux faibles : des corrélations plus fines, fondées sur la recherche

La corrélation moyenne classique est un indicateur *retardé* : quand elle explose, la
crise est déjà là. MarketSignal calcule donc quatre familles de mesures plus fines,
issues de la littérature académique et financière, qui bougent **avant** :

| Mesure | Ce qu'elle capte | Référence |
|---|---|---|
| **Turbulence statistique** (`turbulence_pct`) | Distance de Mahalanobis des rendements du jour : des co-mouvements *inhabituels* même à volatilité basse — typique des débuts de rupture d'approvisionnement | Kritzman & Li (2010), *Skulls, Financial Turbulence, and Risk Management*, Financial Analysts Journal |
| **Choc d'absorption** (`absorption_shift`) | Fraction de variance absorbée par les premières composantes principales : quand elle monte, tout se met à bouger d'un seul bloc et un choc local se propage à tout le système. Un choc > 1 σ a historiquement précédé la majorité des drawdowns sévères | Kritzman, Li, Page & Rigobon (2011), *Principal Components as a Measure of Systemic Risk*, Journal of Portfolio Management |
| **Corrélation baissière & asymétrie** (`downside_correlation`, `correlation_asymmetry`) | Les corrélations conditionnelles aux jours de baisse dépassent celles des jours de hausse à l'approche des crises — un signal que la moyenne dilue | Longin & Solnik (2001), Journal of Finance ; Ang & Chen (2002), Journal of Financial Economics |
| **Densité du réseau de Granger** (`granger_density`) | Fraction des paires de séries où le passé de l'une prédit l'autre : des canaux de contagion qui s'ouvrent entre maillons de la chaîne | Billio, Getmansky, Lo & Pelizzon (2012), Journal of Financial Economics |
| **Relations avance/retard** (`/risk/lead-lag`) | Quelles séries *mènent* les autres et avec quel délai : surveiller l'amont donne des jours d'avance sur l'aval | Approche des indicateurs avancés du Global Supply Chain Pressure Index, Fed de New York (Benigno, di Giovanni, Groen & Noble, 2022) |

Ces mesures alimentent le score composite, le modèle prédictif et le moteur d'alertes
(codes `TURBULENCE`, `FRAGILITE_SYSTEMIQUE`, `ASYMETRIE_BAISSIERE`, `CONTAGION`).

### Quelles séries suivre pour anticiper une crise de chaîne d'approvisionnement ?

MarketSignal accepte n'importe quelles séries journalières. Pour la surveillance
d'une chaîne d'approvisionnement, la recherche (notamment la construction du GSCPI de
la Fed de New York) recommande de mélanger des séries **amont** et **aval** :

- **Coûts de transport** : Baltic Dry Index (vrac sec), Harpex (conteneurs),
  Freightos Baltic Index (FBX), indices de fret aérien du BLS — historiquement les
  séries les plus *en avance* sur les tensions.
- **Enquêtes PMI** : délais de livraison des fournisseurs, carnets de commandes,
  stocks d'achats (ISM, S&P Global) des pays de vos fournisseurs.
- **Matières premières critiques** pour votre production (énergie, métaux,
  semi-conducteurs via les indices sectoriels).
- **Devises** des pays fournisseurs et **indices actions sectoriels** de vos clients
  (l'aval) — c'est la relation amont → aval que la matrice avance/retard mesure.
- **Le GSCPI lui-même** (mensuel, publié par la Fed de New York) comme série de
  contexte macro.

Une fois ces colonnes dans votre CSV, la matrice avance/retard vous dit par exemple
« le fret conteneurs mène votre indice sectoriel de 4 jours » : c'est votre fenêtre
d'anticipation.

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
├── data.py          # Chargement CSV + générateur synthétique (régimes de crise, structure meneur/suiveur)
├── indicators.py    # Indicateurs d'alerte précoce
├── weak_signals.py  # Signaux faibles : turbulence, absorption, corrélations conditionnelles, Granger, lead-lag
├── scoring.py       # Score de risque composite 0–100
├── model.py         # Modèle ML de prédiction de crise (validation temporelle)
├── alerts.py        # Moteur d'alertes métier
├── api.py           # API FastAPI + tableau de bord HTML
└── cli.py           # Interface en ligne de commande
```

## Références

- Kritzman, M. & Li, Y. (2010). *Skulls, Financial Turbulence, and Risk Management*. Financial Analysts Journal, 66(5).
- Kritzman, M., Li, Y., Page, S. & Rigobon, R. (2011). *Principal Components as a Measure of Systemic Risk*. Journal of Portfolio Management, 37(4).
- Billio, M., Getmansky, M., Lo, A. & Pelizzon, L. (2012). *Econometric Measures of Connectedness and Systemic Risk in the Finance and Insurance Sectors*. Journal of Financial Economics, 104(3).
- Ang, A. & Chen, J. (2002). *Asymmetric Correlations of Equity Portfolios*. Journal of Financial Economics, 63(3).
- Longin, F. & Solnik, B. (2001). *Extreme Correlation of International Equity Markets*. Journal of Finance, 56(2).
- Benigno, G., di Giovanni, J., Groen, J. & Noble, A. (2022). *The GSCPI: A New Barometer of Global Supply Chain Pressures*. Federal Reserve Bank of New York Staff Reports, n° 1017 — <https://www.newyorkfed.org/research/policy/gscpi>

## Suivi du projet

- **[ROADMAP.md](ROADMAP.md)** — vision et jalons (v0.3 : données réelles ; v0.4 :
  rigueur statistique ; v0.5 : exploitation ; v1.0 : production).
- **[SUIVI.md](SUIVI.md)** — tableau de bord des actions, journal et limites connues.
- **[CHANGELOG.md](CHANGELOG.md)** — historique des versions.
- **[Issues GitHub](https://github.com/faycaltaha/MarketSignal/issues)** — suivi
  opérationnel de chaque chantier.

## Avertissement

MarketSignal est un outil d'aide à la décision : il fournit des probabilités et des signaux,
pas des certitudes. Il ne constitue pas un conseil financier.
