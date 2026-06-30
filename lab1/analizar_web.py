#!/usr/bin/env python3
"""Analiza lab1/access.log (Combined Log Format de Apache): detecta escaneo
de directorios, agrupa códigos 4xx/5xx por IP, detecta posibles SQL
Injection y exporta reporte_web.json."""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

LOG_PATH = Path("lab1/access.log")
OUTPUT_PATH = Path("lab1/reporte_web.json")

VENTANA_ESCANEO_SEG = 60
UMBRAL_RUTAS_ESCANEO = 20

SQLI_PATTERNS = [r"UNION", r"SELECT", r"--", r"OR\s+1=1", r"'"]
SQLI_RE = re.compile("|".join(SQLI_PATTERNS), re.IGNORECASE)

COMBINED_RE = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<fecha>[^\]]+)\] '
    r'"(?P<metodo>\S+) (?P<ruta>\S+) (?P<protocolo>[^"]+)" '
    r'(?P<status>\d{3}) (?P<size>\S+)'
)

FECHA_FMT = "%d/%b/%Y:%H:%M:%S %z"


def parsear_linea(linea: str):
    match = COMBINED_RE.match(linea)
    if not match:
        return None
    datos = match.groupdict()
    try:
        datos["timestamp"] = datetime.strptime(datos["fecha"], FECHA_FMT)
    except ValueError:
        return None
    datos["status"] = int(datos["status"])
    return datos


def detectar_escaneo_directorios(registros):
    por_ip = defaultdict(list)
    for r in registros:
        por_ip[r["ip"]].append(r)

    escaneos = []
    for ip, eventos in por_ip.items():
        eventos.sort(key=lambda e: e["timestamp"])
        ventana = []
        rutas_vistas_max = 0
        for evento in eventos:
            ventana.append(evento)
            ventana[:] = [
                e for e in ventana
                if (evento["timestamp"] - e["timestamp"]).total_seconds() <= VENTANA_ESCANEO_SEG
            ]
            rutas_distintas = {e["ruta"] for e in ventana}
            rutas_vistas_max = max(rutas_vistas_max, len(rutas_distintas))

        if rutas_vistas_max > UMBRAL_RUTAS_ESCANEO:
            escaneos.append({"ip": ip, "rutas_distintas_max_ventana": rutas_vistas_max})

    return sorted(escaneos, key=lambda e: e["rutas_distintas_max_ventana"], reverse=True)


def agrupar_errores_por_ip(registros):
    errores = defaultdict(lambda: {"4xx": 0, "5xx": 0})
    for r in registros:
        if 400 <= r["status"] < 500:
            errores[r["ip"]]["4xx"] += 1
        elif 500 <= r["status"] < 600:
            errores[r["ip"]]["5xx"] += 1
    return {ip: counts for ip, counts in errores.items() if counts["4xx"] or counts["5xx"]}


def detectar_sqli(registros):
    hallazgos = []
    for r in registros:
        if SQLI_RE.search(r["ruta"]):
            hallazgos.append({
                "ip": r["ip"],
                "ruta": r["ruta"],
                "timestamp": r["timestamp"].strftime("%Y-%m-%d %H:%M:%S%z"),
            })
    return hallazgos


def main():
    if not LOG_PATH.exists():
        raise SystemExit(f"No se encontró {LOG_PATH}. Copie access.log a lab1/ primero.")

    registros = []
    with LOG_PATH.open("r", errors="ignore") as f:
        for linea in f:
            r = parsear_linea(linea)
            if r:
                registros.append(r)

    print(f"Líneas parseadas: {len(registros)}")

    escaneos = detectar_escaneo_directorios(registros)
    print(f"\nIPs con escaneo de directorios detectado ({len(escaneos)}):")
    for e in escaneos:
        print(f"  {e['ip']:15s} -> {e['rutas_distintas_max_ventana']} rutas distintas en <{VENTANA_ESCANEO_SEG}s")

    errores_por_ip = agrupar_errores_por_ip(registros)
    print(f"\nIPs con códigos 4xx/5xx ({len(errores_por_ip)}):")
    for ip, counts in errores_por_ip.items():
        print(f"  {ip:15s} -> 4xx: {counts['4xx']}, 5xx: {counts['5xx']}")

    sqli_hallazgos = detectar_sqli(registros)
    print(f"\nPosibles intentos de SQL Injection ({len(sqli_hallazgos)}):")
    for h in sqli_hallazgos:
        print(f"  [SQLi] {h['ip']:15s} -> {h['ruta']}")

    reporte = {
        "fecha_analisis": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_peticiones": len(registros),
        "escaneo_directorios": escaneos,
        "errores_por_ip": errores_por_ip,
        "posibles_sqli": sqli_hallazgos,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)

    print(f"\nReporte exportado a {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
