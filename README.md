# 🛵 Optimización de Rutas de Última Milla — Catering Gourmet

### Fuerza Bruta vs. Algoritmo Voraz aplicado a la distribución de pedidos gourmet en Lima

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?logo=jupyter&logoColor=white)
![Status](https://img.shields.io/badge/Estado-Finalizado-brightgreen)
![License](https://img.shields.io/badge/Uso-Académico-lightgrey)

---

## 📌 Descripción del proyecto

Este proyecto aborda un problema real de **logística de última milla** para un servicio de **catering gourmet** con base en **Barranco, Lima**. El objetivo es comparar dos estrategias algorítmicas para resolver el ruteo de pedidos hacia distintos distritos de la ciudad:

- **Fuerza Bruta**: explora todas las permutaciones posibles de clientes para garantizar la ruta óptima (exacta).
- **Algoritmo Voraz (Greedy)**: construye la ruta paso a paso eligiendo en cada momento al cliente más conveniente según una función de costo, priorizando velocidad de cómputo sobre la garantía de optimalidad.

El análisis contempla restricciones reales del negocio: **capacidad de carga**, **ventanas de tiempo de entrega**, **cadena de frío**, **peajes** y **tráfico en hora punta**, evaluando en qué escenarios conviene cada enfoque.

---

## 🧠 Algoritmos implementados

### 1. Fuerza Bruta (exacta)
Evalúa **todas las permutaciones** `n!` de los clientes seleccionados, validando en cada una:
- Capacidad máxima de peso y volumen por mochila.
- Cumplimiento de ventanas horarias de cada cliente.
- Cumplimiento de la cadena de frío.

Devuelve la ruta de **menor tiempo total** entre todas las combinaciones factibles. Garantiza la solución óptima, pero su costo computacional crece factorialmente con el número de clientes.

### 2. Algoritmo Voraz (heurístico)
Construye la ruta de forma incremental, seleccionando en cada paso al cliente con **menor costo combinado**, calculado como:

```
costo = (distancia × peso_distancia) + (urgencia × peso_urgencia) + (perecibilidad × peso_perecibilidad)
```

Si ningún cliente restante es factible con la unidad actual, se despacha una **nueva moto** desde la base. Es mucho más rápido que la fuerza bruta, aunque no garantiza la ruta óptima global.

---

## ⚙️ Reglas y restricciones del modelo

| Parámetro | Valor |
|---|---|
| Capacidad máxima de peso | 20 kg por mochila |
| Capacidad máxima de volumen | 30 L por mochila |
| Tiempo máximo de cadena de frío | 2 horas |
| Costo de peaje | S/. 7.50 por tramo |
| Hora de salida | 12:00 pm |
| Franja de hora punta | 12:00 pm – 3:00 pm (factor 1.6x) |
| Factor de circuidad | 1.3 (distancia real vs. línea recta) |

La velocidad promedio se ajusta automáticamente según la cantidad de clientes (más nodos → más tráfico → menor velocidad).

**Distritos considerados:** Barranco (base), San Isidro, Miraflores, Santiago de Surco, San Borja, La Molina, Lince, San Luis, Miraflores-Financiero y Miraflores-Larcomar.

---

## 📁 Estructura del repositorio

```
├── FB_vs_VR_notebook.ipynb   # Notebook con el análisis comparativo completo
├── implementacion.py         # Script ejecutable en modo interactivo por consola
└── README.md
```

---

## 🚀 Cómo ejecutar el proyecto

### Opción 1: Notebook (análisis completo)
```bash
jupyter notebook FB_vs_VR_notebook.ipynb
```

### Opción 2: Script interactivo por consola
```bash
python implementacion.py
```

El script te guiará paso a paso:
1. Selección de los distritos/clientes a atender (por ID).
2. Ingreso de datos por pedido: peso, volumen, ventana horaria, tiempo de servicio y nivel de perecibilidad.
3. Ejecución automática de ambos algoritmos.
4. Tabla comparativa final con tiempos, distancias, peajes y CPU de cada enfoque.

> ⚠️ Con 8 o más clientes, el sistema advierte que la Fuerza Bruta puede tardar bastante (por el crecimiento factorial de permutaciones) y pregunta si deseas ejecutarla igual.

---

## 📊 Métricas comparadas

Para cada algoritmo se reportan:

- ⏱️ Tiempo de ejecución (CPU, en ms)
- 🕒 Tiempo total de ruta (horas)
- 📏 Distancia total recorrida (km)
- 💰 Costo de peajes (S/.)
- 📦 Clientes atendidos vs. omitidos
- ✅ Indicador de si la solución obtenida es óptima

---

## 🛠️ Tecnologías utilizadas

- **Python 3**
- **Jupyter Notebook**
- Librerías estándar: `itertools`, `math`, `time`, `re`

---

## 👩‍💻 

Proyecto desarrollado por el **GRUPO 4**, como parte de un análisis comparativo aplicado a un caso real de distribución de última milla.
