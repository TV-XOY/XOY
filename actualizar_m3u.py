import os
import subprocess

# Configuración basada en tu línea real
URL_OKRU = "https://ok.ru"
ARCHIVO_M3U = "otro-repo/XOY"  
NOMBRE_TVG = "OK Live"  # Coincide exactamente con tvg-name="OK Live"

def obtener_enlace_m3u8():
    try:
        print("Extrayendo nueva URL desde OK.ru con Streamlink...")
        resultado = subprocess.run(
            ["streamlink", URL_OKRU, "best", "--stream-url"],
            capture_output=True, text=True, check=True
        )
        url_extraida = resultado.stdout.strip()
        if "m3u8" in url_extraida:
            print(f"URL extraída con éxito: {url_extraida[:30]}...")
            return url_extraida
        print("Error: El enlace obtenido no contiene 'm3u8'.")
        return None
    except Exception as e:
        print(f"Error crítico al usar Streamlink: {e}")
        return None

def actualizar_linea_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error crítico: El archivo {ARCHIVO_M3U} no existe en la ruta de trabajo.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    nuevas_lineas = []
    modificado = False
    buscar_url = False
    contador_lineas = 0

    print(f"Buscando el canal con tvg-name=\"{NOMBRE_TVG}\" dentro del archivo XOY...")

    for linea in lineas:
        if buscar_url:
            # Reemplazamos la línea de la URL caducada por la nueva m3u8
            nuevas_lineas.append(nueva_url + "\n")
            buscar_url = False
            modificado = True
        else:
            nuevas_lineas.append(linea)
            # Validación exacta buscando la coincidencia del tvg-name
            if "#EXTINF" in linea and f'tvg-name="{NOMBRE_TVG}"' in linea:
                buscar_url = True
                contador_lineas += 1

    if modificado:
        with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
            f.writelines(nuevas_lineas)
        print(f"¡Éxito total! Se localizó tu canal y se actualizó la URL en '{ARCHIVO_M3U}'.")
    else:
        print(f"⚠️ Error de coincidencia: No se encontró la etiqueta tvg-name=\"{NOMBRE_TVG}\".")
        print("Revisa que no existan problemas de codificación o espacios raros en tu archivo XOY.")

if __name__ == "__main__":
    enlace = obtener_enlace_m3u8()
    if enlace:
        actualizar_linea_m3u(enlace)

