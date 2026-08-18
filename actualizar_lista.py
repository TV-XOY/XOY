import os
import subprocess
import re
import json

URL_OK_RU = "https://ok.ru/videoembed/10849691639514?nochat=1&autoplay=1"
ARCHIVO_M3U = "XOY"

def obtener_m3u8():
    try:
        # Extraer credenciales de los Secretos de GitHub (Variables de entorno)
        user = os.environ.get("PROXY_USER")
        pw = os.environ.get("PROXY_PASS")
        host = os.environ.get("PROXY_HOST")
        port = os.environ.get("PROXY_PORT")

        if not all([user, pw, host, port]):
            print("Error: Credenciales de proxy no configuradas en Secrets.")
            return None

        # Construir URL del proxy: http://user:password@host:port
        proxy_url = f"http://{user}:{pw}@{host}:{port}"
        
        print(f"Iniciando extracción a 480p usando Proxy México: {host}")
        
        comando = [
            "yt-dlp",
            URL_OK_RU,
            "-f", "best[height<=480]", # Forzar calidad máxima 480p para estabilidad
            "--dump-json",
            "--no-warnings",
            "--no-check-certificates",
            "--impersonate", "chrome",
            "--proxy", proxy_url,
            "--extractor-args", "okru:player_type=modern"
        ]
        
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        datos_video = json.loads(resultado.stdout)
        
        # Priorizar la URL que coincida con el formato de calidad elegido
        url_extraida = datos_video.get("url")
        if url_extraida and ".m3u8" in url_extraida:
            return url_extraida
        
        return None
            
    except Exception as e:
        print(f"Error al extraer: {e}")
        return None

def actualizar_archivo_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo '{ARCHIVO_M3U}' no existe.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    # Detectar IP de salida para el X-Forwarded-For
    ip_autorizada = os.environ.get("PROXY_HOST", "127.0.0.1")
    match_ip = re.search(r'/srcIp/([^/]+)/', nueva_url)
    if match_ip:
        ip_autorizada = match_ip.group(1)

    bloque_nuevo = [
        '#EXTINF:-1 tvg-name="CANAL13.mx" tvg-chno="13" tvg-id="CANAL13.mx" tvg-logo="https://canal13mexico.com" group-title="NACIONALES",CANAL 13 MERIDA\n',
        '#EXTVLCOPT--http-reconnect=true\n',
        '#EXTVLCOPT:network-caching=3000\n',
        '#KODIPROP:inputstream.adaptive.manifest_type=hls\n',
        f'#EXTVLCOPT:http-x-forwarded-for={ip_autorizada}\n',
        '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\n',
        f'#KODIPROP:inputstream.adaptive.stream_headers=User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36&X-Forwarded-For={ip_autorizada}\n',
        f'{nueva_url}\n'
    ]

    indice_inicio = -1
    for i, linea in enumerate(lineas):
        if "CANAL 13 MERIDA" in linea and "#EXTINF" in linea:
            indice_inicio = i
            break

    if indice_inicio != -1:
        # Buscar el final del bloque (la URL actual)
        indice_fin = -1
        for j in range(indice_inicio + 1, len(lineas)):
            if lineas[j].startswith("http"):
                indice_fin = j
                break
        
        if indice_fin != -1:
            lineas_finales = lineas[:indice_inicio] + bloque_nuevo + lineas[indice_fin + 1:]
        else:
            lineas_finales = lineas + ['\n'] + bloque_nuevo
    else:
        lineas_finales = lineas + ['\n'] + bloque_nuevo

    with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
        f.writelines(lineas_finales)
    print("Archivo XOY actualizado correctamente.")

if __name__ == "__main__":
    url_m3u8 = obtener_m3u8()
    if url_m3u8:
        actualizar_archivo_m3u(url_m3u8)
