# Guía paso a paso — Examen Práctico Seguridad Informática

Esta guía explica, paso a paso, cómo montar el entorno completo en AWS y
ejecutar los 4 laboratorios de principio a fin. Está escrita para que
cualquier persona (no solo el autor) pueda seguirla y reproducir el examen
en una instancia EC2 nueva, entendiendo qué hace cada comando y qué
resultado esperar.

Cada sección de laboratorio termina con la lista de evidencias (capturas)
que ese paso debe producir, y dónde guardarlas en el repositorio.

---

## 0. Por qué este entorno: AWS en vez de una VM local

Todo el examen corre en **una sola instancia EC2** (`t3.medium`, Ubuntu
24.04) que aloja Wazuh, los scripts del Lab 1 y el dashboard del Lab 4; el
Lab 3 (Machine Learning) se hace aparte en **Amazon SageMaker Studio Lab**,
que es gratuito y no consume créditos de la instancia.

¿Por qué no montar todo en una máquina virtual local? Porque Wazuh
All-in-One junto con su stack de búsqueda (OpenSearch/Elastic) necesita en
la práctica 4 GB de RAM sostenidos, y en un sistema como CachyOS (Arch-based)
levantar una VM con salida real a internet implica configurar primero la red
NAT de libvirt:

```bash
sudo pacman -S qemu-full libvirt virt-manager dnsmasq iptables-nft
sudo systemctl enable --now libvirtd
sudo usermod -aG libvirt $USER     # cerrar sesión y volver a entrar para que aplique
virsh net-start default            # activa la red NAT (DHCP/DNS automáticos)
virsh net-autostart default
```

Esto es opcional y solo hace falta si en algún momento quieres probar algo
localmente antes de subirlo a la nube. El resto de esta guía asume que
trabajas directamente sobre la instancia EC2.

---

## 1. Lanzar la instancia EC2

1. Entra a la consola de AWS Educate con tu correo institucional:
   https://aws.amazon.com/education/awseducate/
2. Ve a **EC2 → Launch Instance** y configura:
   - **Nombre:** `wazuh-soc`
   - **Región:** `us-east-1` (N. Virginia) — la región sugerida por el examen
   - **AMI:** Ubuntu Server 24.04 LTS (HVM), 64-bit (x86)
   - **Tipo de instancia:** `t3.medium`
   - **Key pair:** crea una nueva, llámala `wazuh-soc-key`, y descarga el
     archivo `.pem`. En tu equipo, protégelo (SSH se niega a usar una clave
     con permisos demasiado abiertos):
     ```bash
     chmod 400 ~/Descargas/wazuh-soc-key.pem
     ```
   - **Almacenamiento:** 50 GB gp3 (el mínimo que pide el examen)
3. En el **Security Group**, abre estos puertos de entrada:

   | Puerto | Protocolo | Origen | Para qué |
   |---|---|---|---|
   | 22 | TCP | My IP | conectarte por SSH |
   | 443 | TCP | My IP | Wazuh Dashboard / OpenSearch Dashboards (HTTPS) |
   | 1514 | TCP/UDP | My IP | agentes Wazuh (no estorba dejarlo abierto aunque no uses agentes externos) |
   | 1515 | TCP | My IP | enrolamiento de agentes Wazuh |
   | 55000 | TCP | My IP | API REST de Wazuh |

4. Lanza la instancia. Cuando esté en estado `running`, anota su **IP
   pública** — la necesitarás constantemente. Si la detienes y la vuelves a
   iniciar, la IP cambia (salvo que reserves una Elastic IP), así que
   conviene apuntarla cada sesión.

5. Conéctate por SSH:
   ```bash
   ssh -i ~/Descargas/wazuh-soc-key.pem ubuntu@<IP_PUBLICA>
   ```
   Si todo va bien verás un prompt como `ubuntu@ip-172-31-x-x:~$` — ese
   hostname (`ip-172-31-x-x`) es justamente lo que el examen pide que se vea
   en las capturas de pantalla, como prueba de que el trabajo se hizo en la
   nube.

---

## 2. Preparar Git y clonar el repositorio en la instancia

Antes de tocar ningún laboratorio, instala las dependencias base y deja el
repositorio listo dentro de la instancia.

```bash
sudo apt update && sudo apt -y upgrade
sudo apt -y install git python3 python3-pip python3-venv unzip libxml2-utils sshpass
```

`libxml2-utils` es el paquete que trae `xmllint`, que usarás más adelante
para validar las reglas XML de Wazuh.

Configura tu identidad de Git (para que los commits queden a tu nombre):

```bash
git config --global user.name "Jorge Luis Gutierrez Miranda"
git config --global user.email "<tu_correo_institucional>"
```

Si ya creaste el repositorio vacío en GitHub/GitLab con el nombre
`examen-practico`, clónalo directamente:

```bash
git clone https://github.com/TheReeds/examen-practico.git
cd examen-practico
```

Si en cambio ya tienes el contenido armado en local (como en este caso, donde
el esqueleto se generó primero en la máquina de desarrollo) y necesitas
subirlo desde cero, los pasos son:

```bash
cd examen-practico
git init                      # solo si aún no es un repo git
git add -A
git commit -m "Estructura inicial del examen"
git branch -M main
git remote add origin https://github.com/TheReeds/examen-practico.git
git push -u origin main
```

A partir de aquí, cada vez que termines una tarea de un laboratorio, harás
`git add`, `git commit` y `git push` — el examen pide commits frecuentes, no
uno solo al final.

---

## 3. Laboratorio 1 — Análisis forense de logs con Python

### 3.1 Preparar el entorno Python

Usa un entorno virtual para no mezclar paquetes con el sistema:

```bash
cd ~/examen-practico
python3 -m venv .venv
source .venv/bin/activate
pip install pandas matplotlib seaborn
```

### 3.2 Copiar los logs de entrada

El examen entrega dos archivos (`auth.log` y `access.log`) desde el
repositorio del curso, en `examenfinal/lab1/`. Descárgalos a tu máquina
local y súbelos a la instancia con `scp`:

```bash
# Desde tu máquina local (no desde la instancia EC2):
scp -i ~/Descargas/wazuh-soc-key.pem auth.log access.log \
  ubuntu@<IP_PUBLICA>:~/examen-practico/lab1/
```

Confirma que llegaron:

```bash
ls -la lab1/auth.log lab1/access.log
```

### 3.3 Ejecutar analizar_ssh.py

Este script lee `lab1/auth.log`, cuenta los intentos fallidos de SSH por IP,
imprime un ranking de las 10 IPs más agresivas, lanza una alerta en consola
si alguna supera 50 intentos, y guarda todo en `lab1/reporte_ssh.json`.

```bash
python3 lab1/analizar_ssh.py
```

Deberías ver algo como:

```
Total de intentos fallidos: 487
Top 10 IPs con más intentos fallidos:
   1. 203.0.113.45    -> 132 intentos
   ...
[ALERTA] IP: 203.0.113.45 - 132 intentos fallidos - Posible ataque de fuerza bruta
```

📸 Captura la terminal con las líneas `[ALERTA]` visibles y guárdala como
`lab1/evidencias/SCR-1.1a_ssh_ejecucion.png`.

Revisa el JSON generado:

```bash
cat lab1/reporte_ssh.json
```

📸 Captura su contenido como `lab1/evidencias/SCR-1.1b_ssh_json.png`.

### 3.4 Ejecutar analizar_web.py

Este script parsea `lab1/access.log` en formato Combined Log Format,
detecta escaneo de directorios (más de 20 rutas distintas desde la misma IP
en menos de 60 segundos), agrupa los códigos 4xx/5xx por IP, busca patrones
de SQL Injection en la URL (`UNION`, `SELECT`, `--`, `OR 1=1`, `'`), y guarda
el resultado en `lab1/reporte_web.json`.

```bash
python3 lab1/analizar_web.py
```

📸 Captura la terminal mostrando las detecciones de escaneo y SQLi como
`lab1/evidencias/SCR-1.2a_web_ejecucion.png`.

```bash
cat lab1/reporte_web.json
```

📸 Captura su contenido como `lab1/evidencias/SCR-1.2b_web_json.png`.

### 3.5 Generar las gráficas

```bash
python3 lab1/visualizar.py
ls -la lab1/graficas/
```

Esto debe generar tres imágenes dentro de `lab1/graficas/`:
`top10_ssh.png` (barras), `timeline_http.png` (línea de tiempo) y
`heatmap_http.png` (mapa de calor). Estas tres imágenes se entregan tal cual
como archivos PNG en el repositorio — no hace falta capturarlas en pantalla,
ya están en formato evidencia.

### 3.6 Cerrar el laboratorio

```bash
deactivate    # salir del entorno virtual
git add lab1/
git commit -m "Lab1: análisis forense de logs SSH y Web completado"
git push
```

---

## 4. Laboratorio 2 — Reglas de correlación en Wazuh

### 4.1 Instalar Wazuh en modo All-in-One

El instalador oficial de Wazuh levanta en un solo paso el Manager, el
Indexer (OpenSearch) y el Dashboard:

```bash
curl -sO https://packages.wazuh.com/4.x/wazuh-install.sh
sudo bash ./wazuh-install.sh -a
```

La instalación tarda varios minutos. Al terminar, el script imprime en
pantalla la URL del dashboard y una contraseña generada para el usuario
`admin`. Cópiala a un lugar seguro — la necesitarás para entrar al
dashboard en el Laboratorio 4.

Verifica que el manager quedó activo:

```bash
sudo systemctl status wazuh-manager
```

Debe mostrar `active (running)` en verde.

📸 Captura esa salida como `lab2/evidencias/SCR-2.1_wazuh_activo.png`.

### 4.2 Instalar las reglas de correlación personalizadas

Las reglas viven en `/var/ossec/etc/rules/`. Copia los dos archivos XML que
ya están preparados en el repositorio:

```bash
sudo cp lab2/local_rules_ssh.xml /var/ossec/etc/rules/
sudo cp lab2/local_rules_exfil.xml /var/ossec/etc/rules/
```

`local_rules_ssh.xml` detecta fuerza bruta SSH: 10 o más fallos de
autenticación desde la misma IP en una ventana de 60 segundos, usando los
atributos `frequency` y `timeframe` de Wazuh sobre la regla base 5716
(`sshd: authentication failed`).

`local_rules_exfil.xml` es una regla compuesta en dos pasos: primero marca
(sin generar alerta visible) cualquier login SSH exitoso fuera del horario
laboral (22:00–06:00), y luego, si desde esa misma IP se detecta una
transferencia saliente mayor a 500 MB dentro de la hora siguiente, dispara
una alerta de severidad crítica (nivel 14). La lógica completa está
documentada en comentarios dentro del propio archivo XML.

Antes de reiniciar el servicio, valida que el XML esté bien formado —
Wazuh no arranca si hay un error de sintaxis:

```bash
xmllint --noout /var/ossec/etc/rules/local_rules_ssh.xml && echo OK
xmllint --noout /var/ossec/etc/rules/local_rules_exfil.xml && echo OK
```

📸 Captura la salida de ambas validaciones (las dos líneas `OK`) como
`lab2/evidencias/SCR-2.2_reglas_validadas.png`.

Reinicia Wazuh para que cargue las reglas nuevas:

```bash
sudo systemctl restart wazuh-manager
sudo systemctl status wazuh-manager
```

### 4.3 Probar la regla de fuerza bruta

El repositorio incluye `lab2/simular_bruteforce.sh`, que lanza varios
intentos de login SSH fallidos contra la propia instancia para disparar la
regla 100001.

```bash
chmod +x lab2/simular_bruteforce.sh
./lab2/simular_bruteforce.sh ubuntu localhost 12
```

Espera unos segundos a que Wazuh procese los eventos y revisa el log de
alertas:

```bash
sudo tail -n 50 /var/ossec/logs/alerts/alerts.log | grep -A 5 "100001"
```

Deberías ver una entrada con `"rule":{"id":"100001"...` y la IP de origen
(en este caso `127.0.0.1`, ya que el ataque es contra localhost).

📸 Captura ese fragmento del log como
`lab2/evidencias/SCR-2.3_alerta_disparada.png`.

### 4.4 Cerrar el laboratorio

```bash
cd ~/examen-practico
git add lab2/
git commit -m "Lab2: reglas Wazuh de fuerza bruta y exfiltración + evidencia"
git push
```

---

## 5. Laboratorio 3 — Detección de anomalías con ML (SageMaker Studio Lab)

Este laboratorio no se hace en la instancia EC2, sino en **SageMaker Studio
Lab**, que es un entorno Jupyter gratuito de AWS (cuenta separada de AWS
Educate, no consume créditos).

### 5.1 Crear el entorno

1. Regístrate en https://studiolab.sagemaker.aws/ con tu correo.
2. Una vez aprobada la cuenta (puede tardar hasta un día la primera vez),
   inicia un runtime de tipo **CPU** — el dataset es pequeño (10 000 filas) y
   no necesita GPU.
3. Desde la interfaz de JupyterLab, sube tres archivos a una carpeta
   `lab3/` dentro del entorno:
   - `deteccion_anomalias.ipynb` (ya está en el repositorio)
   - `network_traffic.csv` (descárgalo del repo del curso, ruta
     `examenfinal/lab3/network_traffic.csv`)
   - `predecir.py` (ya está en el repositorio)

4. Abre una terminal dentro de Studio Lab e instala las dependencias:
   ```bash
   pip install pandas numpy matplotlib seaborn scikit-learn joblib
   ```

### 5.2 Ejecutar el notebook

Abre `deteccion_anomalias.ipynb` y ejecuta las celdas en orden, de arriba
hacia abajo. El notebook está organizado en 4 bloques que corresponden a las
4 tareas del laboratorio:

- **Exploración y preprocesamiento:** carga el CSV, muestra estadísticas
  descriptivas, grafica histogramas de `bytes_sent` y `duration_sec`,
  limpia nulos y atípicos extremos, crea las variables derivadas
  `ratio_bytes` y `bytes_por_segundo`, y normaliza todo con
  `StandardScaler`.

  📸 Captura las celdas de EDA con los histogramas visibles como
  `lab3/evidencias/SCR-3.1_eda.png`.

- **Entrenamiento del modelo:** entrena un `IsolationForest` con
  `contamination=0.05`, calcula Precision/Recall/F1-Score comparando contra
  la columna `label` (que solo se usa para validar, nunca para entrenar), y
  grafica la matriz de confusión con seaborn.

  📸 Captura la celda con las métricas impresas y la matriz de confusión
  como `lab3/evidencias/SCR-3.2_metricas.png`.

- **Interpretación y umbral dinámico:** grafica el score de anomalía
  (`decision_function`) de todos los registros, prueba distintos umbrales
  para encontrar el que maximiza el F1-Score, y lista los 10 registros más
  anómalos con una explicación en markdown de por qué podrían representar
  una amenaza real.

  📸 Captura la curva umbral-vs-F1 y la tabla de Top 10 como
  `lab3/evidencias/SCR-3.3_umbral_f1.png`.

- **Exportación del modelo:** serializa el modelo entrenado (junto con el
  scaler y la lista de features) en `lab3/modelo_anomalias.pkl` usando
  `joblib`.

### 5.3 Descargar el modelo y probarlo con predecir.py

Desde Studio Lab, descarga `modelo_anomalias.pkl` a tu máquina y colócalo en
`lab3/modelo_anomalias.pkl` dentro de tu copia local del repositorio (o
súbelo también a la instancia EC2 si prefieres ejecutar `predecir.py` ahí).

```bash
cd lab3
python3 predecir.py nuevo_trafico.csv
```

El script carga el modelo, recalcula las mismas features derivadas sobre el
CSV nuevo, y por consola imprime solo los registros que el modelo clasifica
como anomalía, junto con su score.

📸 Captura esa salida como `lab3/evidencias/SCR-3.4_predecir.png`.

### 5.4 Cerrar el laboratorio

```bash
git add lab3/
git commit -m "Lab3: modelo Isolation Forest entrenado, evaluado y exportado"
git push
```

---

## 6. Laboratorio 4 — Dashboard SOC con OpenSearch Dashboards

Se usa **OpenSearch Dashboards**, que ya viene incluido en la instalación
All-in-One de Wazuh del paso 4.1 — no hay que instalar nada adicional, solo
entrar a la URL que mostró el instalador (`https://<IP_PUBLICA>`) con el
usuario `admin` y la contraseña que anotaste.

### 6.1 Conectar la fuente de datos

1. Entra al dashboard y ve a **Stack Management → Index Patterns**.
2. Crea un index pattern llamado `wazuh-alerts-*` (apunta a los índices que
   genera el propio Wazuh con cada alerta).
3. Ve a **Discover** y filtra por las últimas 24 horas para confirmar que
   llegan eventos.
4. Exporta 20 registros representativos a CSV desde la misma vista de
   Discover (botón de exportar/descargar).

📸 Captura la interfaz con la fuente de datos conectada y al menos un evento
visible como `lab4/evidencias/SCR-4.1_fuente_datos.png`.

### 6.2 Crear las 4 visualizaciones

Desde **Visualize → Create visualization**, crea estas cuatro:

| # | Tipo | Qué mide | Cómo agrupar |
|---|---|---|---|
| V1 | Vertical Bar | Conteo de alertas | por `rule.level` |
| V2 | Data Table | Top 10 IPs con más alertas | por `data.srcip` |
| V3 | Line | Alertas por hora (últimas 24h) | por `@timestamp`, intervalo de 1h |
| V4 | Pie Chart | Distribución por tipo de regla | por `rule.groups` |

Guarda cada una con un nombre descriptivo.

📸 Captura las 4 (en un collage o una por una, con nombres
`SCR-4.2a`...`SCR-4.2d`) y guárdalas en `lab4/evidencias/`.

### 6.3 Armar el dashboard integrado

1. Ve a **Dashboard → Create new dashboard**.
2. Añade las 4 visualizaciones del paso anterior.
3. Configura el rango de tiempo global del dashboard a "últimas 24 horas".
4. Agrega un panel de tipo Markdown/Texto con el título y tus datos:
   ```
   # SOC - Monitor de Seguridad
   Autor: Jorge Luis Gutierrez Miranda — UPEU, Ing. Sistemas, ciclo IX
   ```
5. Guarda el dashboard con el nombre exacto **"SOC - Monitor de
   Seguridad"** (el examen lo pide literal).
6. Expórtalo: **Dashboard → Export** y guarda el archivo resultante como
   `lab4/dashboard_soc.json` en el repositorio.

📸 Captura el dashboard completo, con el nombre y los datos del autor
visibles, como `lab4/evidencias/SCR-4.3_dashboard.png`.

### 6.4 Configurar una alerta de umbral

En **Stack Management → Alerting**, crea una regla de tipo threshold:

- Condición: `rule.level >= 10`
- Umbral: más de 5 eventos en una ventana de 5 minutos
- Acción: notificar a un conector tipo Index, llamado `soc-notificaciones`

📸 Captura la regla configurada (con umbral, condición y acción visibles)
como `lab4/evidencias/SCR-4.4_alerta.png`.

### 6.5 Cerrar el laboratorio

```bash
cd ~/examen-practico
cat > lab4/evidencias/herramienta_usada.txt << 'EOF'
OpenSearch Dashboards (incluido en Wazuh 4.x All-in-One)
URL: https://<IP_PUBLICA>
EOF

git add lab4/
git commit -m "Lab4: dashboard SOC en OpenSearch Dashboards con 4 visualizaciones y alerta"
git push
```

---

## 7. Antes de entregar

Repasa esto una última vez antes de pushear el commit final:

- El `README.md` tiene las versiones reales instaladas (no placeholders) y
  el ID de la instancia, región y AMI usados.
- Cada carpeta `evidencias/` tiene todos los screenshots que le
  corresponden, con el nombre exacto que pide la tabla del enunciado
  (prefijo `SCR-<lab>.<tarea>_<descripcion>.png`, todo en minúsculas y sin
  espacios).
- Todos los screenshots muestran la fecha/hora del sistema y el
  hostname/IP de la instancia EC2 (o la URL del servicio) en el prompt o en
  la barra de título — es la prueba de que el trabajo se hizo en la nube.
- El historial de commits muestra trabajo distribuido en el tiempo, no todo
  en un único commit al final.
- `git push` final hecho y el repositorio visible públicamente (o con el
  acceso que pida el profesor) en GitHub/GitLab.
