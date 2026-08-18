import os
import subprocess
import re
import json
import urllib.request

URL_OK_RU = "https://ok.ru/videoembed/10849691639514?nochat=1&autoplay=1"
ARCHIVO_M3U = "XOY"

def obtener_lista_proxies_mexico():
    """Descarga automáticamente los proxies gratuitos activos de México en formato texto"""
    print("Obteniendo lista de proxies gratuitos de México en tiempo real...")
    url_api = "https://es.proxyscrape.com/lista-proxy-gratuita/méxico#free-proxy-table"
    try:
        req = urllib.request.Request(url_api, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            contenido = response.read().decode('utf-8').strip()
            if contenido:
                proxies = [linea.strip() for linea in contenido.split('\n') if linea.strip()]
                print(f"Se encontraron {len(proxies)} proxies de México disponibles.")
                return proxies
    except Exception as e:
        print(f"Error al conectar con la API de proxies: {e}")
    return []

def extraer_con_proxy(proxy_ip_port):
    """Prueba extraer el m3u8 usando un proxy específico"""
    proxy_url = f"http://{proxy_ip_port}"
    comando = [
        "yt-dlp",
        URL_OK_RU,
        "-f", "best[height<=480]",
        "--dump-json",
        "--no-warnings",
        "--no-check-certificates",
        "--force-ipv4",
        "--proxy", proxy_url,
        "--socket-timeout", "15", # Timeout bajo para descartar proxies lentos rápido
        "--extractor-args", "okru:player_type=modern",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ]
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        datos_video = json.loads(resultado.stdout)
        
        url_directa = datos_video.get("url", "")
        if ".m3u8" in url_directa:
            return url_directa
            
        formats = datos_video.get("formats", [])
        for f in reversed(formats):
            url_f = f.get("url", "")
            if ".m3u8" in url_f:
                return url_f
    except Exception:
        # Falla silenciosa para avanzar rápido en la lista si el proxy está muerto o bloqueado
        return None
    return None

def obtener_m3u8():
    lista_proxies = obtener_lista_proxies_mexico()
    if not lista_proxies:
        print("No se pudieron obtener proxies gratuitos. Abortando.")
        return None

    # Recorremos la lista probando uno por uno
    for i, proxy in enumerate(lista_proxies, 1):
        print(f"[{i}/{len(lista_proxies)}] Probando proxy libre: {proxy}...")
        url_final = extraer_con_proxy(proxy)
        if url_final:
            print(f"¡Éxito absoluto! Conectado mediante el proxy funcional: {proxy}")
            return url_final
            
    print("Error: Se probaron todos los proxies de la lista y ninguno logró saltar el bloqueo.")
    return None

def actualizar_archivo_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo '{ARCHIVO_M3U}' no existe.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    ip_autorizada = "127.0.0.1"
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
