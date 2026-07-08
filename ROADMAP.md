# Roadmap MarketSignal

Vision : donner aux entreprises des **jours d'avance** sur les crises qui menacent leur
activité et leur chaîne d'approvisionnement, avec des signaux dont la valeur prédictive
est **prouvée sur des crises réelles**, pas seulement plausible sur le papier.

Le suivi opérationnel des actions se fait dans [SUIVI.md](SUIVI.md) et dans les
[issues GitHub](https://github.com/faycaltaha/MarketSignal/issues). Chaque jalon
ci-dessous liste ses issues de référence.

## ✅ v0.1.0 — Socle (livré)

- Indicateurs d'alerte précoce : volatilité, choc de volatilité, drawdown, momentum,
  corrélation croisée.
- Score de risque composite 0–100 à quatre niveaux.
- Modèle logistique de prédiction de drawdown sévère, validation temporelle, export JSON.
- Moteur d'alertes en français, API FastAPI, tableau de bord web, CLI, générateur de
  données de démonstration, 51 tests.

## ✅ v0.2.0 — Signaux faibles (livré)

- Turbulence statistique (Kritzman & Li, 2010) ; choc d'absorption (Kritzman, Li,
  Page & Rigobon, 2011) ; corrélations conditionnelles baissières et asymétrie
  (Longin & Solnik, 2001 ; Ang & Chen, 2002) ; densité du réseau de causalité de
  Granger (Billio et al., 2012) ; matrice avance/retard.
- Intégration au score, au modèle (AUC démo 0,64 → 0,73), aux alertes, à l'API,
  au tableau de bord et à la CLI. 65 tests.

## 🚧 v0.3.0 — Données réelles (priorité actuelle)

Objectif : sortir du monde synthétique. **Tant que ce jalon n'est pas atteint, les
performances affichées ne doivent pas être présentées à un client.**

| Chantier | Issue |
|---|---|
| Backtest sur crises historiques réelles (2008, COVID, crise logistique 2021-22) | [#1](https://github.com/faycaltaha/MarketSignal/issues/1) |
| Connecteurs de données (FRED, stooq, GSCPI) + fréquences mixtes | [#2](https://github.com/faycaltaha/MarketSignal/issues/2) |
| Direction de stress par série (hausse du fret = stress) | [#3](https://github.com/faycaltaha/MarketSignal/issues/3) |

## 📋 v0.4.0 — Rigueur statistique

Objectif : que chaque signal affiché soit accompagné de sa significativité, et que les
probabilités soient calibrées.

| Chantier | Issue |
|---|---|
| Significativité du lead-lag et de Granger (bootstrap, FDR, Newey-West) | [#4](https://github.com/faycaltaha/MarketSignal/issues/4) |
| Calibration du modèle, précision-rappel, walk-forward, importance des features | [#5](https://github.com/faycaltaha/MarketSignal/issues/5) |
| Vectorisation des signaux faibles pour les grands paniers | [#6](https://github.com/faycaltaha/MarketSignal/issues/6) |

## 📋 v0.5.0 — Exploitation

Objectif : passer de l'outil d'analyse au service qui tourne tous les jours.

| Chantier | Issue |
|---|---|
| Durcissement de l'API : auth, cache, Docker, notifications d'alertes | [#7](https://github.com/faycaltaha/MarketSignal/issues/7) |

## 🎯 v1.0.0 — Production

- Validation documentée sur au moins trois crises historiques avec délais
  d'anticipation mesurés.
- Déploiement conteneurisé chez un premier utilisateur pilote.
- Suivi quotidien automatisé avec notifications.

## Principes de développement

1. **Pas de fuite du futur** : toute évaluation se fait en découpage temporel strict.
2. **Chaque seuil d'alerte cite sa source** (littérature ou backtest interne).
3. **Honnêteté sur les limites** : les performances sur données synthétiques sont
   étiquetées comme telles ; un signal non significatif n'est pas affiché comme un fait.
