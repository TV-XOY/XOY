import os
import subprocess
import re
import json
import sys

URL_OK_RU = "https://ok.ru/videoembed/10849691639514?nochat=1&autoplay=1"
ARCHIVO_M3U = "XOY"

def obtener_m3u8():
    try:
        print("Iniciando extracción a través de Proxy de México público...")
        
        # Usamos un proxy público de México (puedes cambiarlo si se cae)
        # Nota: Los proxies gratuitos fallan a veces, si pasa, prueba otra IP de 'free-proxy-list.net'
        proxy_mexico = "http://187.188.167.161:8080" 
        
        comando = [
            "yt-dlp",
            URL_OK_RU,
            "--dump-json",
            "--no-warnings",
            "--no-check-certificates",
            "--impersonate", "chrome",  
            "--proxy", proxy_mexico,       
            "--extractor-args", "okru:player_type=modern",
            "--socket-timeout", "30" # Damos más tiempo de respuesta
        ]
        
        resultado = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            timeout=120
        )
        
        datos_video = json.loads(resultado.stdout)
        
        url_extraida = datos_video.get("url")
        if url_extraida and ".m3u8" in url_extraida:
            return url_extraida
        
        formats = datos_video.get("formats", [])
        for f in reversed(formats):
            url_formato = f.get("url", "")
            if ".m3u8" in url_formato:
                return url_formato
                
        return None

            
    except subprocess.CalledProcessError as e:
        print(f"Error de yt-dlp (Código {e.returncode}): {e.stderr}")
        return None
    except Exception as e:
        print(f"Error inesperado al extraer: {e}")
        return None

def actualizar_archivo_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error crítico: El archivo '{ARCHIVO_M3U}' no existe. Deteniendo ejecución.")
        sys.exit(1) # Forzar fallo en GitHub Actions para enterarte del problema

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    # IP por defecto si falla el Regex
    ip_autorizada = "190.103.179.109"
    match_ip = re.search(r'/srcIp/([^/]+)/', nueva_url)
    if match_ip:
        ip_autorizada = match_ip.group(1)
        print(f"IP de extracción detectada automáticamente: {ip_autorizada}")

    bloque_nuevo = [
        '#EXTINF:-1 tvg-name="CANAL13.mx" tvg-chno="13" tvg-id="CANAL13.mx" tvg-logo="https://canal13mexico.com" group-title="NACIONALES",CANAL 13 MERIDA\n',
        '#EXTVLCOPT--http-reconnect=true\n',
        '#EXTVLCOPT:network-caching=3000\n',
        '#KODIPROP:inputstream.adaptive.manifest_type=hls\n',
        f'#EXTVLCOPT:http-x-forwarded-for={ip_autorizada}\n',
        '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\n',
        f'#KODIPROP:inputstream.adaptive.stream_headers=User-Agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36&X-Forwarded-For={ip_autorizada}\n',
        f'{nueva_url}\n'
    ]

    indice_inicio = -1
    indice_fin = -1

    for i, linea in enumerate(lineas):
        if "CANAL 13 MERIDA" in linea and "#EXTINF" in linea:
            indice_inicio = i
            break

    if indice_inicio != -1:
        for j in range(indice_inicio + 1, len(lineas)):
            if lineas[j].startswith("http://") or lineas[j].startswith("https://"):
                indice_fin = j
                break
            if lineas[j].startswith("#EXTINF"):
                indice_fin = j - 1
                break

    if indice_inicio != -1 and indice_fin != -1:
        lineas_finales = lineas[:indice_inicio] + bloque_nuevo + lineas[indice_fin + 1:]
        print("¡Éxito! Bloque previo localizado y reemplazado de manera segura.")
    else:
        print("Canal no encontrado previamente. Añadiendo al final de la lista XOY.")
        lineas_finales = lineas + ['\n'] + bloque_nuevo

    with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
        f.writelines(lineas_finales)
    print("Cambios guardados con éxito en tu archivo XOY.")

if __name__ == "__main__":
    url_m3u8 = obtener_m3u8()
    if url_m3u8:
        print(f"URL obtenida con éxito.")
        actualizar_archivo_m3u(url_m3u8)
    else:
        print("Error: No se pudo extraer la URL. Abortando actualización.")
        sys.exit(1) # Informa a GitHub Actions que el workflow falló
