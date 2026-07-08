"""Interface en ligne de commande de MarketSignal.

Commandes : ``demo``, ``analyze``, ``train``, ``serve``.
"""

from __future__ import annotations

import argparse
import sys

from .alerts import evaluate_alerts
from .data import generate_demo_prices, load_prices
from .indicators import compute_indicators
from .model import DEFAULT_HORIZON, DEFAULT_THRESHOLD, CrisisModel
from .scoring import latest_snapshot

INDICATOR_LABELS = {
    "volatility": "Volatilité annualisée (20j)",
    "vol_shock_ratio": "Ratio de choc de volatilité",
    "drawdown": "Drawdown depuis le pic (1 an)",
    "momentum": "Momentum (60j)",
    "mean_correlation": "Corrélation moyenne (60j)",
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="marketsignal",
        description="MarketSignal — anticipation des crises de marché.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_demo = sub.add_parser("demo", help="Génère un CSV de démonstration.")
    p_demo.add_argument("--out", default="demo_prices.csv", help="Chemin du CSV de sortie.")
    p_demo.add_argument("--days", type=int, default=1500, help="Nombre de jours de bourse.")
    p_demo.add_argument("--assets", type=int, default=4, help="Nombre d'actifs.")
    p_demo.add_argument("--seed", type=int, default=42, help="Graine aléatoire.")

    p_analyze = sub.add_parser("analyze", help="Analyse un CSV de prix.")
    p_analyze.add_argument("prices", help="CSV de prix (colonne 'date' + un actif par colonne).")
    p_analyze.add_argument("--model", help="Modèle JSON pré-entraîné (sinon entraîné à la volée).")
    p_analyze.add_argument("--horizon", type=int, default=DEFAULT_HORIZON,
                           help="Horizon de prédiction en jours de bourse.")
    p_analyze.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                           help="Seuil de drawdown définissant une crise (ex. -0.10).")

    p_train = sub.add_parser("train", help="Entraîne le modèle et le sauvegarde en JSON.")
    p_train.add_argument("prices", help="CSV de prix d'entraînement.")
    p_train.add_argument("--model-out", default="model.json", help="Fichier JSON de sortie.")
    p_train.add_argument("--horizon", type=int, default=DEFAULT_HORIZON)
    p_train.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)

    p_serve = sub.add_parser("serve", help="Lance l'API et le tableau de bord web.")
    p_serve.add_argument("prices", help="CSV de prix à surveiller.")
    p_serve.add_argument("--model", help="Modèle JSON pré-entraîné (sinon entraîné au démarrage).")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    return parser


def _cmd_demo(args: argparse.Namespace) -> None:
    df = generate_demo_prices(n_days=args.days, n_assets=args.assets, seed=args.seed)
    df.round(4).to_csv(args.out)
    print(f"Données de démonstration écrites dans {args.out} "
          f"({len(df)} jours, {df.shape[1]} actifs).")


def _cmd_analyze(args: argparse.Namespace) -> None:
    prices = load_prices(args.prices)
    indicators = compute_indicators(prices)
    snapshot = latest_snapshot(indicators)

    if args.model:
        model = CrisisModel.load(args.model)
    else:
        model = CrisisModel(horizon=args.horizon, threshold=args.threshold).fit(prices)
    proba = float(model.predict_proba(indicators.tail(1)).iloc[-1])

    print(f"MarketSignal — analyse au {snapshot.date}")
    print(f"  Actifs suivis : {', '.join(prices.columns)}")
    print()
    print(f"  Score de risque : {snapshot.score:.0f}/100 (niveau {snapshot.level})")
    print(f"  Probabilité de crise (drawdown ≤ {model.threshold:.0%} "
          f"sous {model.horizon}j) : {proba:.0%}")
    if model.auc is not None:
        print(f"  AUC du modèle (validation temporelle) : {model.auc:.2f}")
    print()
    print("  Indicateurs :")
    for key, value in snapshot.indicators.items():
        print(f"    {INDICATOR_LABELS.get(key, key):<32} {value:>8.4f}")
    print()
    print("  Alertes :")
    for alert in evaluate_alerts(snapshot, crisis_probability=proba):
        print(f"    [{alert.severity.upper():<8}] {alert.message}")


def _cmd_train(args: argparse.Namespace) -> None:
    prices = load_prices(args.prices)
    model = CrisisModel(horizon=args.horizon, threshold=args.threshold).fit(prices)
    model.save(args.model_out)
    auc = f"{model.auc:.2f}" if model.auc is not None else "n/a"
    print(f"Modèle entraîné et sauvegardé dans {args.model_out} (AUC test temporel : {auc}).")


def _cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn

    from .api import create_app

    app = create_app(args.prices, model_path=args.model)
    print(f"Tableau de bord : http://{args.host}:{args.port}/")
    uvicorn.run(app, host=args.host, port=args.port)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    handlers = {
        "demo": _cmd_demo,
        "analyze": _cmd_analyze,
        "train": _cmd_train,
        "serve": _cmd_serve,
    }
    try:
        handlers[args.command](args)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
