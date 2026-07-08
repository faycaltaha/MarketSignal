# Changelog

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et le projet
adhère au [versionnage sémantique](https://semver.org/lang/fr/).

## [0.2.0] — 2026-07-08

### Ajouté

- Module `weak_signals.py` : turbulence statistique (Kritzman & Li, 2010), ratio et
  choc d'absorption (Kritzman, Li, Page & Rigobon, 2011), corrélations conditionnelles
  baissières/haussières et asymétrie (Longin & Solnik, 2001 ; Ang & Chen, 2002),
  densité du réseau de causalité de Granger (Billio et al., 2012), matrice
  avance/retard (lead-lag).
- Endpoint `GET /risk/lead-lag` et section « Signaux faibles — qui mène qui ? » du
  tableau de bord.
- Alertes `TURBULENCE`, `FRAGILITE_SYSTEMIQUE`, `ASYMETRIE_BAISSIERE`, `CONTAGION`.
- Structure meneur/suiveur dans le générateur de démonstration (`lead_lag_days`).
- CI GitHub Actions, roadmap (`ROADMAP.md`), suivi d'actions (`SUIVI.md`).

### Modifié

- Le score composite intègre les cinq signaux faibles (nouvelles bornes et pondérations).
- Le modèle prédictif utilise les dix indicateurs comme features (AUC démo 0,64 → 0,73).
- README : section signaux faibles, séries supply chain recommandées, bibliographie.

## [0.1.0] — 2026-07-08

### Ajouté

- Chargement CSV de prix et générateur de données synthétiques à régimes de crise.
- Indicateurs d'alerte précoce : volatilité annualisée, ratio de choc de volatilité,
  drawdown, momentum, corrélation croisée moyenne.
- Score de risque composite 0–100 (niveaux faible/modéré/élevé/critique).
- Modèle logistique de prédiction de drawdown sévère avec validation temporelle et
  sérialisation JSON.
- Moteur d'alertes en français.
- API FastAPI avec tableau de bord web interactif.
- CLI : `demo`, `analyze`, `train`, `serve`.
- Suite de tests (51 tests).
