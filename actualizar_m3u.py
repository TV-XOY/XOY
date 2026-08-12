import os
import subprocess

# Configuración
# Usamos la estructura de live interna porque streamlink la procesa de forma nativa
URL_OKRU = "https://ok.ru/live/10849691639514"  
ARCHIVO_M3U = "XOY"  
IDENTIFICADOR = 'tvg-name="CANAL13.mx"'  # Buscamos solo este parámetro para evitar fallas

def obtener_enlace_m3u8():
    try:
        print("Extrayendo URL dinámica de OK.ru...")
        # Streamlink genera el enlace index.m3u8 de forma automática
        resultado = subprocess.run(
            ["streamlink", URL_OKRU, "best", "--stream-url"],
            capture_output=True, text=True, check=True
        )
        url_extraida = resultado.stdout.strip()
        if "m3u8" in url_extraida:
            print("URL dinámica m3u8 obtenida con éxito.")
            return url_extraida
        print("Error: No se obtuvo un formato m3u8 válido.")
        return None
    except Exception as e:
        print(f"Error en la extracción con Streamlink: {e}")
        return None

def actualizar_linea_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo {ARCHIVO_M3U} no existe.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    nuevas_lineas = []
    modificado = False
    buscar_url = False

    for linea in lineas:
        if buscar_url:
            # Reemplaza la URL caducada vieja por la nueva generada
            nuevas_lineas.append(nueva_url + "\n")
            buscar_url = False
            modificado = True
        else:
            nuevas_lineas.append(linea)
            # Busca si la línea actual del #EXTINF tiene el identificador del canal
            if "#EXTINF" in linea and IDENTIFICADOR in linea:
                buscar_url = True

    if modificado:
        with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
            f.writelines(nuevas_lineas)
        print(f"¡Éxito! El archivo XOY ha sido actualizado debajo de CANAL13.mx.")
    else:
        print(f"⚠️ Error: No se encontró la etiqueta {IDENTIFICADOR} dentro de tu archivo XOY.")

if __name__ == "__main__":
    enlace = obtener_enlace_m3u8()
    if enlace:
        actualizar_linea_m3u(enlace)
