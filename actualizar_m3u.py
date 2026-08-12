import os
import subprocess

# Configuración
URL_OKRU = "https://ok.ru/videoembed/10849691639514?nochat=1&autoplay=1"
# Aponta a la subcarpeta 'otro-repo' y al archivo 'XOY' sin extensión
ARCHIVO_M3U = "XOY/XOY"  
# Ajusta esto al valor exacto de tvg-name que tenga tu canal en la lista
NOMBRE_TVG = "OK Live"  

def obtener_enlace_m3u8():
    try:
        print("Extrayendo nueva URL desde OK.ru...")
        resultado = subprocess.run(
            ["streamlink", URL_OKRU, "best", "--stream-url"],
            capture_output=True,
            text=True,
            check=True
        )
        url_extraida = resultado.stdout.strip()
        if "m3u8" in url_extraida:
            return url_extraida
        return None
    except Exception as e:
        print(f"Error con Streamlink: {e}")
        return None

def actualizar_linea_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo {ARCHIVO_M3U} no existe en la ruta especificada.")
        return

    # Lee el archivo de texto plano XOY
    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    nuevas_lineas = []
    modificado = False
    buscar_url = False

    for linea in lineas:
        if buscar_url:
            # Reemplaza la URL vieja por la nueva
            nuevas_lineas.append(nueva_url + "\n")
            buscar_url = False
            modificado = True
        else:
            nuevas_lineas.append(linea)
            # Detecta tu canal usando el parámetro tvg-name
            if "#EXTINF" in linea and f'tvg-name="{NOMBRE_TVG}"' in linea:
                buscar_url = True

    if modificado:
        with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
            f.writelines(nuevas_lineas)
        print(f"Archivo '{ARCHIVO_M3U}' actualizado internamente con éxito.")
    else:
        print(f"No se encontró el canal con tvg-name='{NOMBRE_TVG}' dentro de XOY.")

if __name__ == "__main__":
    enlace = obtener_enlace_m3u8()
    if enlace:
        actualizar_linea_m3u(enlace)
