# Examen Práctico Final — Seguridad Informática (Unidad IV)

**Autor:** Jorge Luis Gutierrez Miranda
**Universidad:** Universidad Peruana Unión (UPEU)
**Carrera:** Ingeniería de Sistemas — Ciclo IX
**Curso:** Seguridad Informática — Unidad IV: Monitoreo de Seguridad, SIEM e Inteligencia Artificial

> Documentación general del entorno. El paso a paso detallado (comandos exactos,
> capturas y evidencia generada en cada laboratorio) está en [`GUIA.md`](GUIA.md).

## Modalidad de trabajo: AWS Academy / AWS Educate

Se usó AWS Educate como entorno de trabajo (justificación: equipo personal con
recursos limitados para correr Wazuh + Elastic/OpenSearch Stack de forma estable
en local; ver detalle de la decisión en `GUIA.md`).

### Distribución de instancias

| Instancia | Servicio AWS | Uso |
|---|---|---|
| `wazuh-soc` | EC2 t3.medium, Ubuntu 24.04 LTS | Wazuh All-in-One (Manager + Indexer + Dashboard/OpenSearch) — Lab 2 y Lab 4. También aloja y ejecuta los scripts de Python del Lab 1 (`analizar_ssh.py`, `analizar_web.py`, `visualizar.py`) |
| ML / Jupyter | Amazon SageMaker Studio Lab (gratuito) | Lab 3 — notebook `deteccion_anomalias.ipynb` |

- ID de instancia, región, AMI: *(completar en GUIA.md tras el lanzamiento — ver Paso 1)*
- Región usada: `us-east-1`

## Herramientas y versiones instaladas

*(completar a medida que se instala cada herramienta en la instancia — comando sugerido entre paréntesis)*

| Herramienta | Versión | Comando de verificación |
|---|---|---|
| Ubuntu | 24.04 LTS | `lsb_release -a` |
| Python | 3.11+ | `python3 --version` |
| pip / venv | — | `pip3 --version` |
| Wazuh | 4.x (All-in-One) | `/var/ossec/bin/wazuh-control info` |
| OpenSearch Dashboards | — | incluido en Wazuh All-in-One, puerto 443/5601 |
| Git | — | `git --version` |

## Estructura del repositorio

```
examen-practico/
├── README.md
├── GUIA.md                  ← Runbook paso a paso (comandos, evidencias)
├── lab1/                    ← Análisis forense de logs con Python
├── lab2/                    ← Reglas de correlación Wazuh
├── lab3/                    ← Modelo de detección de anomalías (ML)
└── lab4/                    ← Dashboard SOC (OpenSearch Dashboards)
```

## Cómo reproducir cada laboratorio

Ver instrucciones detalladas, comandos exactos y capturas requeridas en
[`GUIA.md`](GUIA.md).
