#!/usr/bin/env python3
"""Genera las 3 gráficas requeridas en lab1/graficas/:
top10_ssh.png, timeline_http.png, heatmap_http.png"""

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

LAB1_DIR = Path("lab1")
GRAFICAS_DIR = LAB1_DIR / "graficas"
GRAFICAS_DIR.mkdir(parents=True, exist_ok=True)

COMBINED_RE = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<fecha>[^\]]+)\] '
    r'"(?P<metodo>\S+) (?P<ruta>\S+) (?P<protocolo>[^"]+)" '
    r'(?P<status>\d{3}) (?P<size>\S+)'
)
FECHA_FMT = "%d/%b/%Y:%H:%M:%S %z"


def graficar_top10_ssh():
    reporte_path = LAB1_DIR / "reporte_ssh.json"
    with reporte_path.open() as f:
        reporte = json.load(f)

    ips = [item["ip"] for item in reporte["ips_sospechosas"]]
    intentos = [item["intentos"] for item in reporte["ips_sospechosas"]]

    plt.figure(figsize=(10, 6))
    sns.barplot(x=intentos, y=ips, hue=ips, palette="rocket", legend=False)
    plt.title("Top 10 IPs con más intentos fallidos SSH")
    plt.xlabel("Intentos fallidos")
    plt.ylabel("IP de origen")
    plt.tight_layout()
    plt.savefig(GRAFICAS_DIR / "top10_ssh.png", dpi=150)
    plt.close()
    print(f"Generado {GRAFICAS_DIR / 'top10_ssh.png'}")


def cargar_access_log():
    registros = []
    with (LAB1_DIR / "access.log").open("r", errors="ignore") as f:
        for linea in f:
            match = COMBINED_RE.match(linea)
            if not match:
                continue
            datos = match.groupdict()
            try:
                datos["timestamp"] = datetime.strptime(datos["fecha"], FECHA_FMT)
            except ValueError:
                continue
            datos["status"] = int(datos["status"])
            registros.append(datos)
    return registros


def graficar_timeline_http(registros):
    por_hora = Counter(r["timestamp"].strftime("%Y-%m-%d %H:00") for r in registros)
    horas_ordenadas = sorted(por_hora.keys())
    conteos = [por_hora[h] for h in horas_ordenadas]

    plt.figure(figsize=(12, 5))
    plt.plot(horas_ordenadas, conteos, marker="o")
    plt.title("Número de peticiones HTTP por hora")
    plt.xlabel("Hora")
    plt.ylabel("Peticiones")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(GRAFICAS_DIR / "timeline_http.png", dpi=150)
    plt.close()
    print(f"Generado {GRAFICAS_DIR / 'timeline_http.png'}")


def graficar_heatmap_http(registros):
    codigos_interes = [200, 301, 404, 500]
    matriz = defaultdict(lambda: defaultdict(int))
    for r in registros:
        if r["status"] in codigos_interes:
            hora = r["timestamp"].hour
            matriz[hora][r["status"]] += 1

    df = pd.DataFrame(matriz).T.reindex(columns=codigos_interes, fill_value=0)
    df = df.reindex(range(24), fill_value=0).sort_index()

    plt.figure(figsize=(8, 10))
    sns.heatmap(df, annot=True, fmt="d", cmap="YlOrRd")
    plt.title("Peticiones HTTP por hora y código de respuesta")
    plt.xlabel("Código de respuesta")
    plt.ylabel("Hora del día")
    plt.tight_layout()
    plt.savefig(GRAFICAS_DIR / "heatmap_http.png", dpi=150)
    plt.close()
    print(f"Generado {GRAFICAS_DIR / 'heatmap_http.png'}")


def main():
    graficar_top10_ssh()
    registros = cargar_access_log()
    graficar_timeline_http(registros)
    graficar_heatmap_http(registros)


if __name__ == "__main__":
    main()
