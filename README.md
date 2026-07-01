# Examen Práctico Final — Seguridad Informática (Unidad IV)

**Autor:** Jorge Luis Gutierrez Miranda
**Universidad:** Universidad Peruana Unión (UPEU)
**Carrera:** Ingeniería de Sistemas — Ciclo IX
**Curso:** Seguridad Informática — Unidad IV: Monitoreo de Seguridad, SIEM e Inteligencia Artificial

> Documentación general del entorno. El paso a paso detallado (comandos exactos,
> capturas y evidencia generada en cada laboratorio) está en [`GUIA.md`](GUIA.md).
> La versión con las capturas de pantalla ya insertadas en cada paso está en
> [`GUIA realizada.docx`](GUIA%20realizada.docx) — mismo contenido que
> `GUIA.md`, pero como documento Word con la evidencia visual incrustada.

## Modalidad de trabajo: AWS Educate → entorno local (cambio a mitad de examen)

El examen empezó en **AWS Educate**: una instancia EC2 alojaba Wazuh All-in-One
(Manager + Indexer + Dashboard/OpenSearch) para los laboratorios 1, 2 y 4, y
Amazon SageMaker Studio Lab se usó para el Lab 3 (ver justificación completa
de por qué AWS en vez de una VM local en `GUIA.md`, sección 0).

A mitad del examen, **UPEU cerró el curso y la cuenta de AWS Educate quedó
suspendida sin acceso** (no una sesión expirada — la cuenta misma dejó de
estar disponible). Los Laboratorios 1 y 2 ya estaban completos y evidenciados
en ese momento (capturas + commits pusheados desde la EC2), así que esa
evidencia se mantiene tal cual. Los Laboratorios 3 y 4 se completaron
**en local, sobre el mismo equipo de trabajo (CachyOS)**, sin usar ninguna
VM: Lab 3 en un entorno virtual de Python (`venv`) con Jupyter, y Lab 4 con
Wazuh corriendo en Docker (proyecto oficial `wazuh-docker`).

Esto está amparado explícitamente en el enunciado del examen
(`EvaluacionPractica.pdf`, sección "Modalidad AWS Education"): AWS es una
opción para quien no cuente con recursos suficientes en su equipo (mínimo
8 GB RAM / 4 vCPU / 50 GB disco); este equipo (16 GB RAM, 16 núcleos, 250+ GB
libres) supera ese mínimo, así que el entorno local es igual de válido —
la modalidad AWS nunca fue un requisito obligatorio, solo una alternativa.

### Distribución de instancias / entornos

| Laboratorio | Entorno | Uso |
|---|---|---|
| Lab 1 y Lab 2 | EC2 `t3.medium`, Ubuntu 24.04 LTS (AWS Educate, región `us-east-1`) | Wazuh All-in-One (Manager + Indexer + Dashboard/OpenSearch), scripts de Python del Lab 1 (`analizar_ssh.py`, `analizar_web.py`, `visualizar.py`) |
| Lab 3 | `venv` de Python local (`~/venvs/examen-lab3`, fuera del repo) | Notebook `deteccion_anomalias.ipynb`, `predecir.py` |
| Lab 4 | Docker local (`wazuh-docker` v4.14.0, modo `single-node`) | Wazuh Manager + Indexer + Dashboard (OpenSearch Dashboards), corriendo en `https://localhost:443` |

- ID de instancia EC2, región y AMI usados para Lab 1-2: no recuperables tras
  la suspensión de la cuenta (no se guardó el ID exacto antes del corte de
  acceso); la evidencia de que la instancia existió y estuvo activa es la
  propia captura `lab2/evidencias/SCR-2.1_wazuh_activo.png`, tomada en vivo
  sobre esa instancia, con su hostname visible en el prompt.
- Región usada: `us-east-1`. AMI: Ubuntu Server 24.04 LTS (HVM), 64-bit (x86). Tipo: `t3.medium`.

## Herramientas y versiones instaladas

| Herramienta | Versión | Dónde | Comando de verificación |
|---|---|---|---|
| Ubuntu | 24.04 LTS | EC2 (Lab 1-2) | `lsb_release -a` |
| Wazuh | 4.x (All-in-One) | EC2 (Lab 1-2) | `/var/ossec/bin/wazuh-control info` |
| Python | 3.11+ (EC2) / 3.14.4 (local) | EC2 y local | `python3 --version` |
| pip / venv | — | EC2 y local | `pip3 --version` |
| scikit-learn | 1.9.0 | venv local (Lab 3) | `pip show scikit-learn` |
| pandas | 3.0.3 | venv local (Lab 3) | `pip show pandas` |
| seaborn | 0.13.2 | venv local (Lab 3) | `pip show seaborn` |
| Jupyter / nbconvert | — | venv local (Lab 3) | `jupyter --version` |
| Docker | 29.5.0 | local (Lab 4) | `docker --version` |
| Docker Compose | v5.1.3 | local (Lab 4) | `docker compose version` |
| Wazuh (manager/indexer/dashboard) | 4.14.0 | Docker local (Lab 4) | `docker compose ps` en `~/wazuh-docker/single-node` |
| OpenSearch Dashboards | incluido en `wazuh/wazuh-dashboard:4.14.0` | Docker local (Lab 4), puerto `443` | acceso vía navegador |
| Git | — | ambos | `git --version` |

## Metodología de evidencias

Cada captura sigue la convención `SCR-<lab>.<tarea>_<descripcion>.png` y
muestra fecha/hora del sistema y el hostname/prompt visible, como prueba de
ejecución real (requisito del enunciado):

- **Lab 1 y Lab 2:** capturas tomadas en vivo dentro de la instancia EC2
  (prompt con el hostname de la instancia), antes del cierre de acceso a AWS.
- **Lab 3:** capturas tomadas en el navegador local (notebook Jupyter ya
  ejecutado vía `nbconvert`) y en la terminal local (`predecir.py`), con el
  prompt del propio equipo visible en vez de un hostname EC2 — documentado
  así explícitamente porque el laboratorio se movió de entorno.
- **Lab 4:** capturas de `docker compose ps` (stack activo), del log de
  alertas real generado (`alerts.log` con la regla `100051` disparando), y
  de la interfaz de OpenSearch Dashboards en `https://localhost:443` —
  mismo criterio: prompt/URL local en vez de IP pública EC2.

## Docker local vs. VM: por qué no se usó una máquina virtual para Lab 4

El Lab 4 podría haberse resuelto igual con una VM local (libvirt/QEMU, ver
`GUIA.md` sección 0) en vez de Docker. Se prefirió Docker por tres motivos
prácticos, aunque ambas opciones son válidas para el enunciado:

- **Menor arranque en frío:** una VM necesita instalar un SO completo desde
  cero (o restaurar una imagen) antes de instalar Wazuh; los contenedores de
  `wazuh-docker` ya traen Wazuh preinstalado en la imagen — se está
  levantando el servicio en minutos, no reinstalando un sistema operativo.
- **Reversibilidad total y más simple:** `docker compose down -v` borra
  contenedores, imágenes y volúmenes de datos en un solo comando; con una VM
  hay que además desmontar la red NAT de libvirt y borrar el disco virtual.
- **Menor huella de recursos:** los contenedores comparten el kernel del
  host (namespaces/cgroups) en vez de virtualizar hardware completo, así que
  consumen menos RAM/CPU en reposo — relevante porque el stack de Wazuh
  (especialmente el Indexer/OpenSearch) ya es pesado por sí solo.

La contrapartida real de Docker frente a una VM: **aislamiento más débil**.
Una VM tiene su propio kernel, completamente separado del host (aislamiento
fuerte a nivel de hipervisor); un contenedor comparte el kernel del host, así
que una fuga de un contenedor comprometido tiene, en teoría, más superficie
de ataque hacia el sistema anfitrión que un escape de VM. Para este examen
—un entorno de laboratorio local, sin exposición a internet, con datos
sintéticos— esa diferencia de aislamiento no es un riesgo relevante, pero es
la razón por la que en un despliegue productivo de Wazuh normalmente se opta
por VMs o por Docker con hardening adicional (rootless, seccomp estricto,
red aislada), no por Docker "por defecto" como se usó aquí.

## Estructura del repositorio

```
examen-practico/
├── README.md
├── GUIA.md                  ← Runbook paso a paso (comandos, evidencias)
├── GUIA realizada.docx      ← Misma guía, con las capturas ya insertadas en cada paso
├── lab1/                    ← Análisis forense de logs con Python
├── lab2/                    ← Reglas de correlación Wazuh
├── lab3/                    ← Modelo de detección de anomalías (ML)
└── lab4/                    ← Dashboard SOC (OpenSearch Dashboards)
```

## Cómo reproducir cada laboratorio

Ver instrucciones detalladas y comandos exactos en [`GUIA.md`](GUIA.md), o
la misma guía con las capturas de evidencia ya incrustadas en cada paso en
[`GUIA realizada.docx`](GUIA%20realizada.docx).
