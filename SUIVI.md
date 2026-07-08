# Suivi des actions

Journal de bord du projet : ce qui a été fait, ce qui est en cours, ce qui est décidé.
Les actions à faire vivent dans les [issues GitHub](https://github.com/faycaltaha/MarketSignal/issues)
et sont rattachées aux jalons de la [ROADMAP](ROADMAP.md) ; ce fichier en donne la vue
d'ensemble et l'historique.

## Tableau de bord des actions

| # | Action | Jalon | Priorité | Statut | Référence |
|---|---|---|---|---|---|
| A1 | Socle : indicateurs, score, modèle, alertes, API, dashboard, CLI | v0.1.0 | — | ✅ Fait (2026-07-08) | commit `8378f6b` |
| A2 | Signaux faibles académiques + lead-lag + intégration complète | v0.2.0 | — | ✅ Fait (2026-07-08) | commit `ffc9bbb` |
| A3 | CI GitHub Actions (pytest, Python 3.10/3.12) | v0.2.0 | — | ✅ Fait (2026-07-08) | `.github/workflows/ci.yml` |
| A4 | Backtest sur crises historiques réelles | v0.3.0 | 🔴 Haute | ⬜ À faire | [#1](https://github.com/faycaltaha/MarketSignal/issues/1) |
| A5 | Connecteurs de données réelles + fréquences mixtes | v0.3.0 | 🔴 Haute | ⬜ À faire | [#2](https://github.com/faycaltaha/MarketSignal/issues/2) |
| A6 | Direction de stress configurable par série | v0.3.0 | 🔴 Haute | ⬜ À faire | [#3](https://github.com/faycaltaha/MarketSignal/issues/3) |
| A7 | Significativité statistique lead-lag / Granger | v0.4.0 | 🟠 Moyenne-haute | ⬜ À faire | [#4](https://github.com/faycaltaha/MarketSignal/issues/4) |
| A8 | Calibration du modèle + métriques événements rares | v0.4.0 | 🟡 Moyenne | ⬜ À faire | [#5](https://github.com/faycaltaha/MarketSignal/issues/5) |
| A9 | Vectorisation des signaux faibles | v0.4.0 | 🟢 Basse | ⬜ À faire | [#6](https://github.com/faycaltaha/MarketSignal/issues/6) |
| A10 | Durcissement production de l'API | v0.5.0 | 🟡 Moyenne | ⬜ À faire | [#7](https://github.com/faycaltaha/MarketSignal/issues/7) |

Statuts : ⬜ À faire · 🔄 En cours · ✅ Fait · ❌ Abandonné

## Journal

### 2026-07-08

- **Livré v0.1.0** : socle complet du logiciel (commit `8378f6b`). 51 tests.
- **Livré v0.2.0** : signaux faibles fondés sur la littérature (Kritzman & Li ;
  Kritzman, Li, Page & Rigobon ; Ang & Chen ; Longin & Solnik ; Billio et al. ;
  approche GSCPI). AUC démo 0,64 → 0,73 (commit `ffc9bbb`). 65 tests.
- **Organisation du suivi** : création de la roadmap, de ce journal, du changelog,
  de la CI et des issues #1 à #7.
- **Revue critique du livrable** : limites identifiées et converties en issues —
  voir la section « limites connues » ci-dessous.

## Limites connues (issues de la revue critique du 2026-07-08)

1. **Validation uniquement synthétique** — les performances (AUC 0,73) sont mesurées
   sur des données générées par un processus qui contient précisément les mécanismes
   que les indicateurs détectent. → [#1](https://github.com/faycaltaha/MarketSignal/issues/1)
2. **Orientation « baisse = stress » inadaptée aux séries amont** — une flambée du
   fret est un stress mais produit aujourd'hui un signal calme. → [#3](https://github.com/faycaltaha/MarketSignal/issues/3)
3. **Lead-lag et Granger sans tests de significativité** — risque élevé de faux
   positifs par sélection du maximum parmi des dizaines de corrélations. → [#4](https://github.com/faycaltaha/MarketSignal/issues/4)
4. **Probabilités non calibrées** — le « 39 % de probabilité de crise » n'a pas été
   confronté à une courbe de calibration. → [#5](https://github.com/faycaltaha/MarketSignal/issues/5)
5. **Fréquences mixtes non gérées** — suivre le GSCPI mensuel comme recommandé dans
   le README fausserait les mesures journalières. → [#2](https://github.com/faycaltaha/MarketSignal/issues/2)
6. **Boucles Python non vectorisées** — inadapté au-delà de ~10 actifs × 10 ans. → [#6](https://github.com/faycaltaha/MarketSignal/issues/6)
7. **API non durcie** — pas d'auth, pas de rafraîchissement des données, recalculs
   à chaque hit. → [#7](https://github.com/faycaltaha/MarketSignal/issues/7)
