import os
import subprocess
import re
import json

URL_OK_RU = "https://ok.ru/videoembed/10849691639514?nochat=1&autoplay=1"
ARCHIVO_M3U = "XOY"

def obtener_m3u8():
    try:
        print("Iniciando extracción a través de la Red Tor (Túnel Regional México)...")
        
        proxy_tor = "socks5://127.0.0.1:9050"
        
        comando = [
            "yt-dlp",
            URL_OK_RU,
            "--dump-json",
            "--no-warnings",
            "--no-check-certificates",
            "--impersonate", "chrome",  
            "--proxy", proxy_tor,       
            "--extractor-args", "okru:player_type=modern"
        ]
        
        resultado = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            timeout=120  # Aumentamos a 2 minutos para asegurar la conexión del nodo MX
        )
        
        datos_video = json.loads(resultado.stdout)
        
        # Intento 1: Buscar URL directa
        url_extraida = datos_video.get("url")
        if url_extraida and ".m3u8" in url_extraida:
            print(f"¡Éxito Absoluto! URL obtenida mediante Tor-MX: {url_extraida}")
            return url_extraida
        
        # Intento 2: Buscar en formatos internos
        formats = datos_video.get("formats", [])
        for f in reversed(formats):
            url_formato = f.get("url", "")
            if ".m3u8" in url_formato:
                print(f"¡Éxito Absoluto! URL localizada en formatos: {url_formato}")
                return url_formato
                
        print("yt-dlp leyó la respuesta pero el stream no contenía un manifiesto HLS (.m3u8).")
        return None
            
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Error crítico en la ejecución de yt-dlp sobre la red Tor.")
        print(f"Detalle técnico de la consola: {e.stderr.strip()}\n")
        return None
    except subprocess.TimeoutExpired:
        print("\n[ERROR] La conexión regional a través de Tor excedió el tiempo límite (Timeout).\n")
        return None
    except Exception as e:
        print(f"Error inesperado en el script: {e}")
        return None

def actualizar_archivo_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo '{ARCHIVO_M3U}' no se encuentra en la raíz.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        contenido = f.read()

    parametros_fijos = (
        '#EXTINF:-1 tvg-name="CANAL13.mx" tvg-chno="13" tvg-id="CANAL13.mx" '
        'tvg-logo="https://canal13mexico.com/wp-content/uploads/2024/04/cropped-LOGO-CANAL-TRECE.png" '
        'group-title="NACIONALES",CANAL 13 MERIDA\n'
        '#EXTVLCOPT:network-caching=2000\n'
        '#EXTVLCOPT--http-reconnect=true\n'
        '#KODIPROP:inputstream.adaptive.manifest_type=hls'
    )

    patron = r'(#EXTINF:-1.*?CANAL 13 MERIDA\n.*?(?:#EXTVLCOPT.*?)\n(?:#KODIPROP.*?)\n)(https?://[^\s]+)'
    
    if re.search(patron, contenido):
        nuevo_contenido = re.sub(patron, f"\\1{nueva_url}", contenido)
        print("Estructura localizada. URL actualizada correctamente en el bloque.")
    else:
        print("No se encontró el bloque exacto. Añadiendo canal al final del archivo.")
        nuevo_contenido = contenido.rstrip() + f"\n\n{parametros_fijos}\n{nueva_url}\n"

    with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
        f.write(nuevo_contenido)
    print("Cambios guardados con éxito en el archivo XOY.")

if __name__ == "__main__":
    url_m3u8 = obtener_m3u8()
    if url_m3u8:
        actualizar_archivo_m3u(url_m3u8)
    else:
        print("No se modificó el archivo debido a las restricciones de la conexión.")
