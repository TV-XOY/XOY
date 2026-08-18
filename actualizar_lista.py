import os
import subprocess
import re
import json
import urllib.parse

URL_OK_RU = "https://ok.ru/videoembed/10849691639514?nochat=1&autoplay=1"
ARCHIVO_M3U = "XOY"

def obtener_m3u8():
    try:
        # Extraer credenciales de los Secrets de GitHub
        user = os.environ.get("PROXY_USER", "")
        pw = os.environ.get("PROXY_PASS", "")
        host = os.environ.get("PROXY_HOST", "")
        port = os.environ.get("PROXY_PORT", "")

        if not all([user, pw, host, port]):
            print("Error: Credenciales de proxy incompletas en variables de entorno.")
            return None

        # Codificación limpia para evitar rotura de URL por caracteres especiales
        user_encoded = urllib.parse.quote(user, safe='')
        pw_encoded = urllib.parse.quote(pw, safe='')

        proxy_url = f"http://{user_encoded}:{pw_encoded}@{host}:{port}"
        
        print(f"Iniciando extracción mediante túnel limpio con Proxy México: {host}")
        
        comando = [
            "yt-dlp",
            URL_OK_RU,
            "-f", "best[height<=480]",
            "--dump-json",
            "--no-warnings",
            "--no-check-certificates",
            "--force-ipv4",
            "--proxy", proxy_url,
            
            # --- PARÁMETROS ANTIBLOQUEO REMOTO ---
            "--http-chunk-size", "10M",             # Divide la petición para engañar al firewall
            "--legacy-server-connect",              # Forzar negociación TLS clásica compatible
            "--socket-timeout", "45",
            "--retries", "3",
            "--extractor-args", "okru:player_type=modern",
            
            # Cabecera simulada idéntica a un navegador real sin rastro de scripts
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "--add-header", "Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "--add-header", "Accept-Language:es-MX,es;q=0.9,en;q=0.8"
        ]
        
        # Ejecutamos el subproceso capturando la salida limpia
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        datos_video = json.loads(resultado.stdout)
        
        # Búsqueda flexible de la URL .m3u8 en la respuesta limpia
        url_directa = datos_video.get("url", "")
        if ".m3u8" in url_directa:
            return url_directa
            
        formats = datos_video.get("formats", [])
        for f in reversed(formats):
            url_f = f.get("url", "")
            if ".m3u8" in url_f:
                return url_f
        
        print("Error: No se encontró ningún formato .m3u8 en la respuesta.")
        return None

    except subprocess.CalledProcessError as e:
        print(f"\n--- ERROR DE ENLACE / YT-DLP ---")
        print(f"Código de salida: {e.returncode}")
        print(f"Detalle del error (stderr):\n{e.stderr}")
        return None
    except Exception as e:
        print(f"Error inesperado: {e}")
        return None

def actualizar_archivo_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo '{ARCHIVO_M3U}' no existe en la raíz.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    # Intentar extraer la IP real de transmisión que asignó el proxy
    ip_autorizada = os.environ.get("PROXY_HOST", "127.0.0.1")
    match_ip = re.search(r'/srcIp/([^/]+)/', nueva_url)
    if match_ip:
        ip_autorizada = match_ip.group(1)
        print(f"IP real de streaming detectada: {ip_autorizada}")

    bloque_nuevo = [
        '#EXTINF:-1 tvg-name="CANAL13.mx" tvg-chno="13" tvg-id="CANAL13.mx" tvg-logo="https://canal13mexico.com" group-title="NACIONALES",CANAL 13 MERIDA\n',
        '#EXTVLCOPT--http-reconnect=true\n',
        '#EXTVLCOPT:network-caching=3000\n',
        '#KODIPROP:inputstream.adaptive.manifest_type=hls\n',
        f'#EXTVLCOPT:http-x-forwarded-for={ip_autorizada}\n',
        '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36\n',
        f'#KODIPROP:inputstream.adaptive.stream_headers=User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36&X-Forwarded-For={ip_autorizada}\n',
        f'{nueva_url}\n'
    ]

    indice_inicio = -1
    for i, linea in enumerate(lineas):
        if "CANAL 13 MERIDA" in linea and "#EXTINF" in linea:
            indice_inicio = i
            break

    if indice_inicio != -1:
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
    print("Cambios guardados con éxito en tu archivo XOY.")

if __name__ == "__main__":
    url_final = obtener_m3u8()
    if url_final:
        actualizar_archivo_m3u(url_final)
