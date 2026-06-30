#!/usr/bin/env python3
"""Carga modelo_anomalias.pkl y clasifica un CSV nuevo de tráfico de red.

Uso:
    python predecir.py nuevo_trafico.csv
"""

import sys
from pathlib import Path

import joblib
import pandas as pd

MODELO_PATH = Path(__file__).parent / "modelo_anomalias.pkl"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python predecir.py <archivo_csv>")

    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        raise SystemExit(f"No se encontró el archivo: {csv_path}")

    paquete = joblib.load(MODELO_PATH)
    modelo = paquete["modelo"]
    scaler = paquete["scaler"]
    features = paquete["features"]

    df = pd.read_csv(csv_path)

    df["ratio_bytes"] = df["bytes_sent"] / df["bytes_recv"].replace(0, 1)
    df["bytes_por_segundo"] = (df["bytes_sent"] + df["bytes_recv"]) / df["duration_sec"].replace(0, 1)

    X = df[features]
    X_scaled = scaler.transform(X)

    df["score"] = modelo.decision_function(X_scaled)
    df["prediccion"] = modelo.predict(X_scaled)

    anomalias = df[df["prediccion"] == -1].sort_values("score")

    print(f"Registros analizados: {len(df)}")
    print(f"Anomalías detectadas: {len(anomalias)}\n")

    if anomalias.empty:
        print("No se detectaron anomalías.")
        return

    columnas_mostrar = [c for c in ["timestamp", "src_ip", "dst_ip", "dst_port", "protocol", "score"] if c in anomalias.columns]
    for _, fila in anomalias.iterrows():
        valores = "  ".join(f"{c}={fila[c]}" for c in columnas_mostrar)
        print(f"[ANOMALIA] {valores}")


if __name__ == "__main__":
    main()
