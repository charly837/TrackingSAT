from uagents import Agent, Context
from sgp4.api import Satrec, jday
from datetime import datetime, timedelta
import math
import requests
import csv
import os
import urllib.request
import json

# ----------------------------
# CONFIGURACIÓN
# ----------------------------

ANTENA_LAT = 40.4168
ANTENA_LON = -3.7038

CELESTRAK_LISTAS = {
    "active": "https://celestrak.org/NORAD/elements/active.txt",
    "gps": "https://celestrak.org/NORAD/elements/gps-ops.txt",
    "starlink": "https://celestrak.org/NORAD/elements/starlink.txt",
    "weather": "https://celestrak.org/NORAD/elements/weather.txt",
    "iridium": "https://celestrak.org/NORAD/elements/iridium.txt",
    "oneweb": "https://celestrak.org/NORAD/elements/oneweb.txt",
    "science": "https://celestrak.org/NORAD/elements/science.txt",
    "visual": "https://celestrak.org/NORAD/elements/visual.txt",
    "geosync": "https://celestrak.org/NORAD/elements/geosync.txt",
    "engineering": "https://celestrak.org/NORAD/elements/engineering.txt",
    "education": "https://celestrak.org/NORAD/elements/education.txt",
    "amateur": "https://celestrak.org/NORAD/elements/amateur.txt",
    "leo": "https://celestrak.org/NORAD/elements/leo.txt",
    "satnogs": "https://celestrak.org/NORAD/elements/satnogs.txt"
}

sat_tracker = Agent(
    name="satellite_tracker",
    seed="seed_unica_para_tu_agente_multi_001"
)

R_EARTH = 6378.137  # Radio de la Tierra (km)

# ----------------------------
# CARGAR SATCAT (país y operador)
# ----------------------------

def cargar_satcat():
    url = "https://celestrak.org/NORAD/elements/supplemental/satcat.csv"
    response = requests.get(url)
    satcat = {}
    if response.status_code == 200:
        lines = response.text.strip().split("\n")
        reader = csv.DictReader(lines)
        for row in reader:
            norad = row["NORAD_CAT_ID"].strip()
            country = row["COUNTRY_OF_OWNER"].strip()
            operator = row["OPERATOR_OWNER"].strip()
            satcat[norad] = (country, operator)
    return satcat

SATCAT = cargar_satcat()

# ----------------------------
# FUNCIONES
# ----------------------------

def obtener_tles():
    satelites = []
    for grupo, url in CELESTRAK_LISTAS.items():
        response = requests.get(url)
        if response.status_code != 200:
            continue
        lines = response.text.strip().split("\n")
        for i in range(0, len(lines) - 2, 3):
            nombre = lines[i].strip()
            tle1 = lines[i + 1].strip()
            tle2 = lines[i + 2].strip()
            norad = tle1[2:7]  # NORAD ID
            satelites.append((grupo, nombre, tle1, tle2, norad))
    return satelites

def leer_epoch_tle(tle1):
    year = int(tle1[18:20])
    if year < 57:
        year += 2000
    else:
        year += 1900
    day_of_year = float(tle1[20:32])
    fecha = datetime(year, 1, 1) + timedelta(days=day_of_year - 1)
    return fecha

def calcular_posicion_geografica(tle1, tle2, fecha):
    satelite = Satrec.twoline2rv(tle1, tle2)
    jd, fr = jday(fecha.year, fecha.month, fecha.day, fecha.hour, fecha.minute, fecha.second)
    error, r, v = satelite.sgp4(jd, fr)
    if error != 0:
        return None
    x, y, z = r
    lon = math.atan2(y, x)
    hyp = math.sqrt(x ** 2 + y ** 2)
    lat = math.atan2(z, hyp)
    lon_deg = math.degrees(lon)
    lat_deg = math.degrees(lat)
    if lon_deg > 180:
        lon_deg -= 360
    alt = hyp - R_EARTH
    return lat_deg, lon_deg, alt

def calcular_azimut_elevacion(lat_sat, lon_sat, alt_km):
    lat_ant = math.radians(ANTENA_LAT)
    lon_ant = math.radians(ANTENA_LON)
    lat_sat = math.radians(lat_sat)
    lon_sat = math.radians(lon_sat)
    dlon = lon_sat - lon_ant

    x = math.cos(lat_sat) * math.sin(dlon)
    y = math.cos(lat_ant) * math.sin(lat_sat) - math.sin(lat_ant) * math.cos(lat_sat) * math.cos(dlon)

    azimut = math.atan2(x, y)
    azimut_deg = (math.degrees(azimut) + 360) % 360

    distancia = distancia_geodesica(ANTENA_LAT, ANTENA_LON, math.degrees(lat_sat), math.degrees(lon_sat), alt_km)
    elevacion = math.atan2(alt_km * 1000, distancia * 1000)
    elevacion_deg = math.degrees(elevacion)

    return azimut_deg, elevacion_deg, distancia


def distancia_geodesica(lat1, lon1, lat2, lon2, alt_km):
    R = 6371.0  # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    base_distance = R * c
    return math.sqrt(base_distance ** 2 + alt_km ** 2)

def calcular_trayectoria(tle1, tle2, fecha_inicio, minutos=90, paso_min=10):
    puntos = []
    for i in range(0, minutos + 1, paso_min):
        fecha = fecha_inicio + timedelta(minutes=i)
        pos = calcular_posicion_geografica(tle1, tle2, fecha)
        if pos:
            lat, lon, alt = pos
            puntos.append((lon, lat, alt * 1000))  # en metros
    return puntos

    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    base_distance = R * c
    return math.sqrt(base_distance ** 2 + alt_km ** 2)


def crear_kml(lista_posiciones):
    kml_inicio = """<?xml version='1.0' encoding='UTF-8'?>
<kml xmlns='http://www.opengis.net/kml/2.2'>
<Document>
"""
    kml_fin = "</Document></kml>"
    placemarks = ""
    ahora = datetime.utcnow()

    for sat in lista_posiciones:
        grupo, nombre, lat, lon, alt, az, el, dist, country, operator, tle1, tle2 = sat
        desc = (
            f"<strong>Nombre:</strong> {nombre}<br>"
            f"<strong>Grupo:</strong> {grupo}<br>"
            f"<strong>Altitud:</strong> {alt:.2f} km<br>"
            f"<strong>País:</strong> {country}<br>"
            f"<strong>Operador:</strong> {operator}<br>"
            f"<strong>Latitud:</strong> {lat:.2f}°<br>"
            f"<strong>Longitud:</strong> {lon:.2f}°<br>"
            f"<strong>Azimut (desde antena):</strong> {az:.2f}°<br>"
            f"<strong>Elevación:</strong> {el:.2f}°<br>"
            f"<strong>Distancia antena-satélite:</strong> {dist:.2f} km"
        )

        placemark = f"""
<Placemark>
  <name>{nombre} ({grupo})</name>
  <description><![CDATA[{desc}]]></description>
  <Point>
    <coordinates>{lon},{lat},{alt * 1000}</coordinates>
  </Point>
</Placemark>
"""
        placemarks += placemark

        trayectoria = calcular_trayectoria(tle1, tle2, ahora)
        if len(trayectoria) > 1:
            coords = " ".join([f"{lon},{lat},{alt}" for lon, lat, alt in trayectoria])
            linea = f"""
<Placemark>
  <name>Órbita de {nombre} ({grupo})</name>
  <Style><LineStyle><color>ff0000ff</color><width>2</width></LineStyle></Style>
  <LineString>
    <tessellate>1</tessellate>
    <coordinates>
      {coords}
    </coordinates>
  </LineString>
</Placemark>
"""
            placemarks += linea

    with open("satellite_positions.kml", "w", encoding="utf-8") as file:
        file.write(kml_inicio + placemarks + kml_fin)
    return "satellite_positions.kml"


# ----------------------------
# COMPORTAMIENTO DEL AGENTE
# ----------------------------

def crear_alerta(nombre, grupo, dist):
    alerta = {
        "nombre": nombre,
        "grupo": grupo,
        "distancia": dist
    }
    with open("alerta.json", "w", encoding="utf-8") as f:
        json.dump(alerta, f)

crear_alerta("SATÉLITE DE PRUEBA", "test", 123.45)


@sat_tracker.on_interval(period=180.0)
async def seguimiento(ctx: Context):
    posiciones = []
    ahora = datetime.utcnow()
    ctx.logger.info(f"Calculando posiciones y datos de {len(SATELITES)} satélites...")

    for grupo, nombre, tle1, tle2, norad in SATELITES:

        try:
            epoch = leer_epoch_tle(tle1)
            dias_desde_epoch = (datetime.utcnow() - epoch).days
        except Exception as e:
            ctx.logger.warning(f"No se pudo leer epoch de {nombre}: {e}")
            continue

        if dias_desde_epoch > 30:
            ctx.logger.info(f"TLE antiguo para {nombre} (epoch hace {dias_desde_epoch} días). Ignorado.")
            continue

        pos = calcular_posicion_geografica(tle1, tle2, ahora)
        if pos:
            lat, lon, alt = pos

            if alt < 100:
                ctx.logger.info(f"{nombre}: altitud {alt:.2f} km demasiado baja. Ignorado.")
                continue

            country, operator = SATCAT.get(norad, ("Desconocido", "Desconocido"))
            az, el, dist = calcular_azimut_elevacion(lat, lon, alt)
            posiciones.append((grupo, nombre, lat, lon, alt, az, el, dist, country, operator, tle1, tle2))
            ctx.logger.info(f"{nombre} ({grupo}) - Alt: {alt:.2f} km - Az: {az:.2f}° El: {el:.2f}° Dist: {dist:.2f} km")

            if dist < 500:
                ctx.logger.info(f"¡ALERTA! {nombre} ({grupo}) está a {dist:.2f} km de la estación base.")
                crear_alerta(nombre, grupo, dist)

    archivo_kml = crear_kml(posiciones)
    ctx.logger.info(f"KML actualizado: {archivo_kml} con {len(posiciones)} satélites.")

SATELITES = obtener_tles()


if __name__ == "__main__":
    sat_tracker.run()

