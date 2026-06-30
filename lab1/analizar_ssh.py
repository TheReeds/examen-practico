#!/usr/bin/env python3
"""Analiza lab1/auth.log: cuenta intentos fallidos de SSH por IP, genera
alertas de fuerza bruta y exporta reporte_ssh.json."""

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

LOG_PATH = Path("lab1/auth.log")
OUTPUT_PATH = Path("lab1/reporte_ssh.json")
UMBRAL_ALERTA = 50
TOP_N = 10

FAILED_RE = re.compile(
    r"Failed password.*from (?P<ip>\d{1,3}(?:\.\d{1,3}){3})"
)


def parsear_auth_log(path: Path) -> Counter:
    contador = Counter()
    with path.open("r", errors="ignore") as f:
        for linea in f:
            if "Failed password" not in linea:
                continue
            match = FAILED_RE.search(linea)
            if match:
                contador[match.group("ip")] += 1
    return contador


def construir_reporte(contador: Counter) -> dict:
    total_fallidos = sum(contador.values())
    top_ips = contador.most_common(TOP_N)

    ips_sospechosas = []
    for ip, intentos in top_ips:
        alerta = intentos > UMBRAL_ALERTA
        if alerta:
            print(f"[ALERTA] IP: {ip} - {intentos} intentos fallidos - Posible ataque de fuerza bruta")
        ips_sospechosas.append({"ip": ip, "intentos": intentos, "alerta": alerta})

    return {
        "fecha_analisis": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_intentos_fallidos": total_fallidos,
        "ips_sospechosas": ips_sospechosas,
    }


def main():
    if not LOG_PATH.exists():
        raise SystemExit(f"No se encontró {LOG_PATH}. Copie auth.log a lab1/ primero.")

    contador = parsear_auth_log(LOG_PATH)

    print(f"Total de intentos fallidos: {sum(contador.values())}")
    print(f"\nTop {TOP_N} IPs con más intentos fallidos:")
    for i, (ip, intentos) in enumerate(contador.most_common(TOP_N), start=1):
        print(f"  {i:2d}. {ip:15s} -> {intentos} intentos")

    reporte = construir_reporte(contador)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)

    print(f"\nReporte exportado a {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
