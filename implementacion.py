import itertools
import time
import math
import re

# =============================================================================
# 1. PARAMETROS FIJOS DEL SISTEMA (NO MODIFICABLES POR EL USUARIO)
# =============================================================================
CAPACIDAD_PESO_MAX    = 20.0      # kg por mochila
CAPACIDAD_VOLUMEN_MAX = 30.0      # litros por mochila
TIEMPO_FRIO_MAX       = 2.0       # horas maximas de cadena de frio
COSTO_PEAJE           = 7.50      # Soles por tramo con peaje
HORA_SALIDA           = 12.0      # 12:00 h
FRANJA_HORA_PICO      = (12.0, 15.0)
FACTOR_HORA_PICO      = 1.60
FACTOR_CIRCUIDAD      = 1.30      # factor de correccion de distancia en linea recta a distancia real

# Pesos para la funcion de costo del Voraz
PESO_DISTANCIA        = 0.3
PESO_URGENCIA         = 0.4
PESO_PERECIBILIDAD    = 0.3

# =============================================================================
# 2. CATALOGO DE UBICACIONES (coordenadas GPS reales aproximadas)
# =============================================================================
CATALOGO_UBICACIONES = {
    1:  {"nombre": "Barranco (Cocina Central)", "lat": -12.1499, "lon": -77.0203},
    2:  {"nombre": "San Isidro",                "lat": -12.0969, "lon": -77.0362},
    3:  {"nombre": "Miraflores",                "lat": -12.1211, "lon": -77.0294},
    4:  {"nombre": "Santiago de Surco",         "lat": -12.1350, "lon": -76.9931},
    5:  {"nombre": "San Borja",                 "lat": -12.1085, "lon": -76.9980},
    6:  {"nombre": "La Molina",                 "lat": -12.0851, "lon": -76.9420},
    7:  {"nombre": "Lince",                     "lat": -12.0850, "lon": -77.0356},
    8:  {"nombre": "San Luis",                  "lat": -12.0698, "lon": -76.9975},
    9:  {"nombre": "Miraflores-Financiero",     "lat": -12.0958, "lon": -77.0257},
    10: {"nombre": "Miraflores-Larcomar",       "lat": -12.1319, "lon": -77.0296},
}

# Distritos con peaje desde la base (Barranco)
DISTRITOS_CON_PEAJE_DESDE_BASE = {4, 6}  # Santiago de Surco, La Molina

def nombre_ubicacion(cid):
    return CATALOGO_UBICACIONES.get(cid, {}).get("nombre", str(cid))

# =============================================================================
# 3. FUNCIONES AUXILIARES
# =============================================================================

def haversine_km(lat1, lon1, lat2, lon2):
    """Distancia en linea recta (km) entre dos coordenadas GPS."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def velocidad_segun_nodos(n):
    """Velocidad promedio (km/h) estimada segun cantidad de clientes.
        Mas nodos => mas trafico/paradas => menor velocidad."""
    if n <= 3:
        return 25.0
    elif n <= 6:
        return 22.0
    elif n <= 10:
        return 18.0
    else:
        return 15.0

def calcular_tiempo_efectivo(origen, destino, hora, velocidad):
    """
    Calcula tiempo de viaje (h) considerando distancia Haversine,
    factor de circuidad, velocidad base y factor de hora punta.
    """
    u1 = CATALOGO_UBICACIONES[origen]
    u2 = CATALOGO_UBICACIONES[destino]
    dist_km = haversine_km(u1["lat"], u1["lon"], u2["lat"], u2["lon"]) * FACTOR_CIRCUIDAD
    tiempo_base = dist_km / velocidad
    lo, hi = FRANJA_HORA_PICO
    if lo <= hora <= hi:
        return tiempo_base * FACTOR_HORA_PICO
    return tiempo_base

def verificar_peaje(origen, destino):
    if origen == 1 and destino in DISTRITOS_CON_PEAJE_DESDE_BASE:
        return COSTO_PEAJE
    if destino == 1 and origen in DISTRITOS_CON_PEAJE_DESDE_BASE:
        return COSTO_PEAJE
    return 0.0

def validar_cadena_frio(hora):
    return (hora - HORA_SALIDA) <= TIEMPO_FRIO_MAX

def calcular_urgencia(hora, ventana):
    e_i, l_i = ventana
    if hora >= l_i:
        return 1.0
    if hora <= e_i:
        return 0.0
    return (hora - e_i) / (l_i - e_i)

def calcular_costo_voraz(distancia, urgencia, perecibilidad):
    """Funcion de costo combinada con pesos fijos."""
    return (distancia * PESO_DISTANCIA) + (urgencia * PESO_URGENCIA) + (perecibilidad * PESO_PERECIBILIDAD)

def distancia_total_ruta(ruta, velocidad):
    """Calcula la distancia total recorrida en km (sin tiempos de espera)."""
    total = 0.0
    for i in range(len(ruta)-1):
        u1 = CATALOGO_UBICACIONES[ruta[i]]
        u2 = CATALOGO_UBICACIONES[ruta[i+1]]
        dist_km = haversine_km(u1["lat"], u1["lon"], u2["lat"], u2["lon"]) * FACTOR_CIRCUIDAD
        total += dist_km
    return total

def formato_hora_12h(hora_decimal):
    h = int(hora_decimal)
    m = int((hora_decimal - h) * 60)
    if m >= 60:
        h += 1
        m -= 60
    periodo = "AM" if h < 12 else "PM"
    h12 = h % 12
    if h12 == 0:
        h12 = 12
    return f"{h12}:{m:02d} {periodo}"

def parsear_hora_12h(texto):
    t = texto.strip().lower().replace(" ", "")
    m = re.fullmatch(r'(\d{1,2}):?(\d{2})?(am|pm)', t)
    if not m:
        return None
    h = int(m.group(1))
    mnt = int(m.group(2)) if m.group(2) else 0
    periodo = m.group(3)
    if h < 1 or h > 12 or mnt > 59:
        return None
    if periodo == "am":
        h = 0 if h == 12 else h
    else:
        h = 12 if h == 12 else h + 12
    return h + mnt / 60.0

def _normalizar_texto(texto):
    t = texto.strip().lower()
    for a, b in (("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n")):
        t = t.replace(a, b)
    return t.replace("-","").replace(" ","")

# Categorias para entrada del usuario
VOLUMEN_CATEGORIAS = {
    "pequeno": ("Pequeño (~5 L)", 5.0),
    "mediano": ("Mediano (~10 L)", 10.0),
    "grande":  ("Grande (~15 L)", 15.0),
}
VOLUMEN_ATAJOS = {"p":"pequeno","m":"mediano","g":"grande"}

SERVICIO_CATEGORIAS = {
    "rapido": ("Rápido (~3 min)", 0.05),
    "normal": ("Normal (~6 min)", 0.10),
    "lento":  ("Lento (~12 min)", 0.20),
}
SERVICIO_ATAJOS = {"r":"rapido","n":"normal","l":"lento"}

PERECIBILIDAD_CATEGORIAS = {
    "bajo":  ("Bajo", 0.1),
    "medio": ("Medio", 0.5),
    "alto":  ("Alto", 0.9),
}
PERECIBILIDAD_ATAJOS = {"b":"bajo","m":"medio","a":"alto"}

def leer_categoria(prompt, categorias, atajos=None):
    etiquetas = [v[0] for v in categorias.values()]
    opciones = " / ".join(etiquetas)
    while True:
        entrada = input(f"{prompt} [{opciones}]: ")
        clave = _normalizar_texto(entrada)
        if atajos and clave in atajos:
            clave = atajos[clave]
        if clave in categorias:
            return categorias[clave]
        print(f"    * Opcion invalida. Escriba una de: {opciones}")

def leer_float(prompt, minimo=None, maximo=None):
    while True:
        entrada = input(prompt).strip()
        try:
            valor = float(entrada)
        except ValueError:
            print("    * Ingrese un numero valido.")
            continue
        if minimo is not None and valor < minimo:
            print(f"    * El valor debe ser >= {minimo}.")
            continue
        if maximo is not None and valor > maximo:
            print(f"    * El valor debe ser <= {maximo}.")
            continue
        return valor

def leer_ids_clientes(catalogo):
    ids_validos = set(catalogo.keys()) - {1}
    id_min, id_max = min(ids_validos), max(ids_validos)
    while True:
        entrada = input("Ingrese IDs de clientes (ej: 2,3,4): ").strip()
        if not entrada:
            print("    * Debe ingresar al menos un ID.")
            continue
        try:
            ids = [int(x.strip()) for x in entrada.split(",") if x.strip()]
        except ValueError:
            print("    * Formato invalido. Use numeros separados por comas.")
            continue
        if not ids:
            print("    * Debe ingresar al menos un ID.")
            continue
        invalidos = sorted(set(i for i in ids if i not in ids_validos))
        if invalidos:
            print(f"    * IDs invalidos: {invalidos}. Use entre {id_min} y {id_max}.")
            continue
        duplicados = sorted(set(i for i in ids if ids.count(i) > 1))
        if duplicados:
            print(f"    * IDs repetidos: {duplicados}. Elimine duplicados.")
            continue
        return ids

def leer_hora_reloj(prompt):
    while True:
        entrada = input(prompt)
        valor = parsear_hora_12h(entrada)
        if valor is None:
            print("    * Formato invalido. Use HH:MM am/pm, ej: 1:00 pm")
            continue
        return valor

def leer_ventana_tiempo():
    e = leer_hora_reloj("  Hora apertura (ej: 1:00 pm): ")
    while True:
        l = leer_hora_reloj(f"  Hora cierre (mayor a {formato_hora_12h(e)}): ")
        if l <= e:
            print(f"    * Cierre debe ser mayor a apertura ({formato_hora_12h(e)}).")
            continue
        return e, l

def leer_datos_clientes(ids, catalogo):
    data = {}
    for cid in ids:
        nombre = catalogo[cid]["nombre"]
        print(f"\nCliente: {nombre}")
        peso = leer_float("  Peso (kg): ", 0.1, 100.0)
        vol_etq, vol = leer_categoria("  Tamaño", VOLUMEN_CATEGORIAS, VOLUMEN_ATAJOS)
        e, l = leer_ventana_tiempo()
        serv_etq, serv = leer_categoria("  Tiempo de servicio", SERVICIO_CATEGORIAS, SERVICIO_ATAJOS)
        per_etq, per = leer_categoria("  Perecibilidad", PERECIBILIDAD_CATEGORIAS, PERECIBILIDAD_ATAJOS)
        data[cid] = {
            "nombre": nombre,
            "peso": peso,
            "volumen": vol,
            "volumen_etiqueta": vol_etq,
            "ventana": (e, l),
            "servicio": serv,
            "servicio_etiqueta": serv_etq,
            "perecibilidad": per,
            "perecibilidad_etiqueta": per_etq,
        }
    return data

def imprimir_tabla_clientes(clientes_dict, ids, titulo="DATOS INGRESADOS"):
    print(f"\n{'='*90}")
    print(f" {titulo}")
    print(f"{'='*90}")
    print(f" {'ID':<4} {'Nombre':<22} {'Peso':<8} {'Volumen':<16} {'Ventana':<20} {'Servicio':<15} {'Perecib':<10}")
    print(f" {'-'*90}")
    for cid in ids:
        d = clientes_dict[cid]
        e,l = d["ventana"]
        vt = f"{formato_hora_12h(e)} - {formato_hora_12h(l)}"
        print(f" {cid:<4} {d['nombre']:<22} {d['peso']:<8.1f} {d['volumen_etiqueta']:<16} {vt:<20} {d['servicio_etiqueta']:<15} {d['perecibilidad_etiqueta']:<10}")
    print(f"{'='*90}\n")

# =============================================================================
# 4. FUERZA BRUTA 
# =============================================================================

def fuerza_bruta(clientes, clientes_data, velocidad):
    mejor_ruta = None
    menor_t = float('inf')
    mejor_peaje = 0.0
    total = inv_cap = inv_ven = inv_frio = 0

    for perm in itertools.permutations(clientes):
        total += 1
        valida = True
        peso = vol = 0.0
        peaje = 0.0
        nodo_ant = 1
        hora = HORA_SALIDA

        for nodo in perm:
            peso += clientes_data[nodo]["peso"]
            vol += clientes_data[nodo]["volumen"]
            if peso > CAPACIDAD_PESO_MAX or vol > CAPACIDAD_VOLUMEN_MAX:
                valida = False
                inv_cap += 1
                break

            hora += calcular_tiempo_efectivo(nodo_ant, nodo, hora, velocidad)
            hora += clientes_data[nodo]["servicio"]

            e_i, l_i = clientes_data[nodo]["ventana"]
            if hora < e_i:
                hora = e_i
            if hora > l_i:
                valida = False
                inv_ven += 1
                break

            if not validar_cadena_frio(hora):
                valida = False
                inv_frio += 1
                break

            peaje += verificar_peaje(nodo_ant, nodo)
            nodo_ant = nodo

        if valida:
            peaje += verificar_peaje(nodo_ant, 1)
            hora += calcular_tiempo_efectivo(nodo_ant, 1, hora, velocidad)
            tt = hora - HORA_SALIDA
            if tt < menor_t:
                menor_t = tt
                mejor_ruta = [1] + list(perm) + [1]
                mejor_peaje = peaje

    return mejor_ruta, menor_t, mejor_peaje, total, inv_cap, inv_ven, inv_frio

# =============================================================================
# 5. ALGORITMO VORAZ 
# =============================================================================

def algoritmo_voraz_inteligente(clientes, clientes_data, velocidad):
    no_vis = list(clientes)
    # Ordenar clientes por urgencia (ventana mas cercana) y perecibilidad
    no_vis.sort(key=lambda c: (clientes_data[c]["ventana"][1], -clientes_data[c]["perecibilidad"]))

    ruta = [1]
    nodo_act = 1
    hora = HORA_SALIDA
    peso = vol = 0.0
    peaje_t = 0.0
    horas_moto_acum = 0.0
    motos = 1
    rutas_u = [[1]]
    horas_regreso = []

    while no_vis:
        mejor = None
        mejor_c = float('inf')
        mejor_tv = 0.0
        ok = False

        for c in no_vis:
            np = peso + clientes_data[c]["peso"]
            nv = vol + clientes_data[c]["volumen"]
            if np > CAPACIDAD_PESO_MAX or nv > CAPACIDAD_VOLUMEN_MAX:
                continue

            tv = calcular_tiempo_efectivo(nodo_act, c, hora, velocidad)
            llegada = hora + tv + clientes_data[c]["servicio"]
            e_i, l_i = clientes_data[c]["ventana"]
            if llegada < e_i:
                llegada = e_i
            if llegada > l_i:
                continue
            if not validar_cadena_frio(llegada):
                continue

            urg = calcular_urgencia(hora, (e_i, l_i))
            per = clientes_data[c]["perecibilidad"]
            cost = calcular_costo_voraz(tv, urg, per)
            if cost < mejor_c:
                mejor_c = cost
                mejor = c
                mejor_tv = tv
                ok = True

        if not ok:
            # No hay candidato para esta moto -> cerramos moto y abrimos nueva (si no estamos en base)
            if nodo_act != 1:
                # Retornar a base
                peaje_t += verificar_peaje(nodo_act, 1)
                hora += calcular_tiempo_efectivo(nodo_act, 1, hora, velocidad)
                horas_moto_acum += hora - HORA_SALIDA
                horas_regreso.append(hora)
                rutas_u[-1].append(1)
                ruta.append(1)
                # Nueva moto
                nodo_act = 1
                peso = vol = 0.0
                hora = HORA_SALIDA
                motos += 1
                rutas_u.append([1])
            else:
                # Estamos en base y no hay candidato: significa que los clientes restantes son infactibles
                # (ventanas muy ajustadas o capacidad). En ese caso, no podemos atenderlos.
                # Rompemos el bucle y reportamos que no se pudo completar.
                break
        else:
            # Asignar mejor candidato
            peaje_t += verificar_peaje(nodo_act, mejor)
            hora += mejor_tv + clientes_data[mejor]["servicio"]
            e_i, l_i = clientes_data[mejor]["ventana"]
            if hora < e_i:
                hora = e_i
            ruta.append(mejor)
            rutas_u[-1].append(mejor)
            peso += clientes_data[mejor]["peso"]
            vol += clientes_data[mejor]["volumen"]
            no_vis.remove(mejor)
            nodo_act = mejor

    # Cerrar ultima moto
    if nodo_act != 1:
        peaje_t += verificar_peaje(nodo_act, 1)
        hora += calcular_tiempo_efectivo(nodo_act, 1, hora, velocidad)
        horas_moto_acum += hora - HORA_SALIDA
        horas_regreso.append(hora)
        rutas_u[-1].append(1)
        ruta.append(1)
    else:
        # Si nunca se movio, eliminar ruta vacia
        if len(rutas_u[-1]) == 1:
            rutas_u.pop()
            if horas_regreso:
                horas_regreso.pop()

    # Limpiar si la ultima ruta quedo vacia
    if rutas_u and len(rutas_u[-1]) == 1:
        rutas_u.pop()
        if horas_regreso:
            horas_regreso.pop()

    if ruta[-1] != 1:
        ruta.append(1)

    # Determinar si se atendio a todos
    atendidos = [c for sub in rutas_u for c in sub if c != 1]
    omitidos = [c for c in clientes if c not in atendidos]

    return ruta, horas_moto_acum, peaje_t, motos, rutas_u, horas_regreso, omitidos

# =============================================================================
# 6. FUNCION PRINCIPAL (MODO INTERACTIVO)
# =============================================================================

def modo_interactivo():
    print("="*60)
    print("   SISTEMA DE RUTAS - CATERING BARRANCO")
    print("="*60)

    print("\nLOCACIONES DISPONIBLES:")
    for cid, datos in CATALOGO_UBICACIONES.items():
        etiqueta = f"{datos['nombre']} (base)" if cid == 1 else datos['nombre']
        print(f"  {cid:>2}. {etiqueta}")
    print()

    # --- Seleccion de clientes ---
    ids = leer_ids_clientes(CATALOGO_UBICACIONES)

    # --- Datos de cada pedido ---
    print(f"\n{'='*60}")
    print(" DATOS DE CADA PEDIDO")
    print(f"{'='*60}")
    clientes_data = leer_datos_clientes(ids, CATALOGO_UBICACIONES)

    # --- Velocidad calculada segun nodos ---
    n = len(ids)
    velocidad = velocidad_segun_nodos(n)
    print(f"\n  Velocidad promedio estimada para {n} clientes: {velocidad:.1f} km/h")

    # --- Resumen de entrada ---
    imprimir_tabla_clientes(clientes_data, ids, "RESUMEN DE PEDIDOS")
    peso_tot = sum(clientes_data[c]["peso"] for c in ids)
    vol_tot = sum(clientes_data[c]["volumen"] for c in ids)
    print(f"  Demanda total: Peso={peso_tot:.1f} kg | Volumen={vol_tot:.1f} L")
    print(f"  Capacidad: {CAPACIDAD_PESO_MAX} kg | {CAPACIDAD_VOLUMEN_MAX} L")

    n_perms = math.factorial(n)
    print(f"  Permutaciones a evaluar (FB): {n}! = {n_perms:,}")

    # --- Ejecutar Fuerza Bruta (si n <= 8, sino advertencia) ---
    ejecutar_fb = True
    if n >= 8:
        print(f"\n  * Advertencia: N={n} clientes -> {n_perms:,} permutaciones. Puede tardar.")
        resp = input("  ¿Ejecutar Fuerza Bruta? (S/N): ").strip().lower()
        ejecutar_fb = resp in ("s","si","sí","y","yes")

    if ejecutar_fb:
        t0 = time.perf_counter()
        r_fb, t_fb, p_fb, tot, ic, iv, iff = fuerza_bruta(ids, clientes_data, velocidad)
        cpu_fb = (time.perf_counter() - t0) * 1000
    else:
        r_fb = None
        t_fb = p_fb = 0.0
        tot = ic = iv = iff = 0
        cpu_fb = 0.0

    # --- Ejecutar Voraz ---
    t0 = time.perf_counter()
    r_vz, t_vz, p_vz, motos, rutas, hrs_regreso, omitidos = algoritmo_voraz_inteligente(
        ids, clientes_data, velocidad)
    cpu_vz = (time.perf_counter() - t0) * 1000

    # --- Calcular distancias ---
    if r_fb:
        dist_fb = distancia_total_ruta(r_fb, velocidad)
    else:
        dist_fb = 0.0
    dist_vz = distancia_total_ruta(r_vz, velocidad) if r_vz else 0.0

    # --- Mostrar resultados ---
    print(f"\n{'='*60}")
    print(" RESULTADOS")
    print(f"{'='*60}")

    if ejecutar_fb and r_fb:
        print(f"\n[1] FUERZA BRUTA (exacta):")
        print(f"    Ruta: {' -> '.join(nombre_ubicacion(x) for x in r_fb)}")
        print(f"    Tiempo ruta: {t_fb:.2f} h  (salida {formato_hora_12h(HORA_SALIDA)}, regreso {formato_hora_12h(HORA_SALIDA + t_fb)})")
        print(f"    Distancia: {dist_fb:.2f} km")
        print(f"    Peajes: S/. {p_fb:.2f}")
        print(f"    CPU: {cpu_fb:.4f} ms")
        print(f"    Permutaciones evaluadas: {tot:,} | Invalidas: cap={ic}, ventana={iv}, frio={iff}")
    elif ejecutar_fb and not r_fb:
        print(f"\n[1] FUERZA BRUTA: No encontro solucion factible.")
    else:
        print(f"\n[1] FUERZA BRUTA: omitida por decision del usuario.")

    print(f"\n[2] ALGORITMO VORAZ (heuristica):")
    print(f"    Ruta consolidada: {' -> '.join(nombre_ubicacion(x) for x in r_vz)}")
    print(f"    Unidades motorizadas: {motos}")
    for i, (u, hr) in enumerate(zip(rutas, hrs_regreso), 1):
        ruta_txt = " -> ".join(nombre_ubicacion(x) for x in u)
        print(f"      Moto {i}: salida {formato_hora_12h(HORA_SALIDA)}, regreso {formato_hora_12h(hr)}  -  Ruta: {ruta_txt}")
    print(f"    Tiempo real (maximo de motos): {max(hrs_regreso) - HORA_SALIDA if hrs_regreso else 0:.2f} h")
    print(f"    Horas-moto acumuladas: {t_vz:.2f} h")
    print(f"    Distancia total (suma de motos): {dist_vz:.2f} km")
    print(f"    Peajes: S/. {p_vz:.2f}")
    print(f"    CPU: {cpu_vz:.4f} ms")
    if omitidos:
        print(f"    CLIENTES NO ATENDIDOS: {[nombre_ubicacion(o) for o in omitidos]}")
    else:
        print(f"    Clientes atendidos: {len(ids)} (todos)")

    # --- Tabla comparativa ---
    print(f"\n{'='*60}")
    print(" TABLA COMPARATIVA")
    print(f"{'='*60}")
    print(f" {'Algoritmo':<20} {'CPU (ms)':<12} {'Tiempo (h)':<12} {'Distancia (km)':<14} {'Peajes (S/.)':<12} {'Atendidos':<10} {'Optimo?':<8}")
    print(f" {'-'*60}")

    if ejecutar_fb and r_fb:
        print(f" {'Fuerza Bruta':<20} {cpu_fb:<12.4f} {t_fb:<12.2f} {dist_fb:<14.2f} {p_fb:<12.2f} {len(ids):<10} {'Si':<8}")
    elif ejecutar_fb and not r_fb:
        print(f" {'Fuerza Bruta':<20} {cpu_fb:<12.4f} {'---':<12} {'---':<14} {'---':<12} {'---':<10} {'No':<8}")
    else:
        print(f" {'Fuerza Bruta':<20} {'---':<12} {'---':<12} {'---':<14} {'---':<12} {'---':<10} {'No':<8}")

    atendidos_vz = len(ids) - len(omitidos)
    es_optimo = (ejecutar_fb and r_fb and abs(t_vz - t_fb) < 0.001 and atendidos_vz == len(ids))
    print(f" {'Voraz':<20} {cpu_vz:<12.4f} {t_vz:<12.2f} {dist_vz:<14.2f} {p_vz:<12.2f} {atendidos_vz:<10} {'Si' if es_optimo else 'No':<8}")

    if ejecutar_fb and r_fb and atendidos_vz == len(ids):
        dif = ((t_vz - t_fb) / t_fb) * 100
        print(f"\n  Diferencia vs. optimo: {dif:+.1f}%")
        if cpu_vz > 0 and cpu_fb > 0:
            print(f"  Voraz es {cpu_fb / cpu_vz:.0f}x mas rapido en CPU")

    print("\n" + "="*60)
    print(" Fin de la ejecucion.")
    print("="*60)

if __name__ == "__main__":
    modo_interactivo()