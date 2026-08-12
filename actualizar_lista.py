import os
import subprocess
import re

# Configuración de variables
URL_OK_RU = "https://ok.ru/live/10849691639514"
ARCHIVO_M3U = "XOY"  # Reemplaza con "XOY.m3u" si tu archivo tiene extensión

def obtener_m3u8():
    try:
        # Ejecuta streamlink de forma nativa para extraer el streaming link directo
        resultado = subprocess.run(
            ["streamlink", URL_OK_RU, "best", "--stream-url"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        url_extraida = resultado.stdout.strip()
        if ".m3u8" in url_extraida:
            print(f"URL extraída con éxito: {url_extraida}")
            return url_extraida
        else:
            print("No se recibió una URL válida de M3U8.")
            return None
    except Exception as e:
        print(f"Error al ejecutar Streamlink: {e}")
        return None

def actualizar_archivo_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo {ARCHIVO_M3U} no existe en la raíz del repositorio.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        contenido = f.read()

    # Bloque de parámetros fijos proporcionados por el usuario
    parametros_fijos = (
        '#EXTINF:-1 tvg-name="CANAL13.mx" tvg-chno="13" tvg-id="CANAL13.mx" '
        'tvg-logo="https://canal13mexico.com/wp-content/uploads/2024/04/cropped-LOGO-CANAL-TRECE.png" '
        'group-title="NACIONALES",CANAL 13 MERIDA\n'
        '#EXTVLCOPT:network-caching=2000\n'
        '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Mobile Safari/537.36\n'
        '#EXTVLCOPT--http-reconnect=true\n'
        '#KODIPROP:inputstream.adaptive.manifest_type=hls'
    )

    # Expresión regular para buscar el bloque completo de Canal 13 Mérida y reemplazar su URL antigua
    patron = r'(#EXTINF:-1.*?CANAL 13 MERIDA\n.*?(?:#EXTVLCOPT.*?)\n(?:#KODIPROP.*?)\n)(https?://[^\s]+)'
    
    if re.search(patron, contenido):
        # Si encuentra la estructura, reemplaza la URL vieja por la nueva manteniendo las directivas previas
        nuevo_contenido = re.sub(patron, f"\\1{nueva_url}", contenido)
        print("Estructura encontrada. URL actualizada dentro del bloque.")
    else:
        # Fallback de seguridad: Si no encuentra el patrón exacto, lo añade al final del archivo
        print("No se encontró el bloque exacto. Añadiendo el canal al final del archivo.")
        nuevo_contenido = contenido + f"\n{parametros_fijos}\n{nueva_url}\n"

    with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
        f.write(nuevo_contenido)
    print("Archivo m3u modificado y guardado localmente.")

if __name__ == "__main__":
    url_m3u8 = obtener_m3u8()
    if url_m3u8:
        actualizar_archivo_m3u(url_m3u8)
