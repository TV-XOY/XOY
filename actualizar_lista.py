import os
import subprocess
import re
import json
import urllib.request

URL_OK_RU = "https://ok.ru/videoembed/10849691639514?nochat=1&autoplay=1"
ARCHIVO_M3U = "XOY"

def obtener_lista_proxies_mexico():
    """Obtiene proxies vivos filtrados estrictamente por el país México (MX) desde APIs abiertas"""
    print("Obteniendo lista dinámica de proxies gratuitos ubicados en México...")
    proxies_encontrados = set()
    
    # API pública directa de Geonode (Filtra solo país MX, protocolos HTTP/HTTPS y los más rápidos)
    url_api = "https://geonode.com"
    
    try:
        req = urllib.request.Request(url_api, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=12) as response:
            datos = json.loads(response.read().decode('utf-8'))
            
            # Extraemos las IPs de la respuesta estructurada de la API
            for proxy_item in datos.get("data", []):
                ip = proxy_item.get("ip")
                port = proxy_item.get("port")
                if ip and port:
                    proxies_encontrados.add(f"{ip}:{port}")
                    
    except Exception as e:
        print(f"Aviso: Error al consultar la API de proxies Geonode ({e})")

    # Respaldo alternativo: API de PubProxy filtrada por México
    try:
        url_respaldo = "http://pubproxy.com"
        req_res = urllib.request.Request(url_respaldo, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_res, timeout=10) as response:
            contenido = response.read().decode('utf-8').strip()
            for linea in contenido.split('\n'):
                if ":" in linea and not "<" in linea: # Evita capturar código HTML residual
                    proxies_encontrados.add(linea.strip())
    except Exception:
        pass

    lista_final = list(proxies_encontrados)
    print(f"Búsqueda finalizada. Se encontraron {len(lista_final)} proxies residenciales/públicos en México.")
    return lista_final

def extraer_con_proxy(proxy_ip_port):
    """Intenta obtener el enlace m3u8 utilizando un proxy específico"""
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
        "--socket-timeout", "14", # Timeout ágil para saltar rápido proxies caídos
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
        return None
    return None

def obtener_m3u8():
    lista_proxies = obtener_lista_proxies_mexico()
    if not lista_proxies:
        print("Error crítico: No se pudieron recolectar IPs de México. Abortando flujo.")
        return None

    # Escanea la lista buscando un proxy activo que venza el bloqueo regional de OK.ru
    for i, proxy in enumerate(lista_proxies, 1):
        print(f"[{i}/{len(lista_proxies)}] Probando túnel regional en MX: {proxy}...")
        url_final = extraer_con_proxy(proxy)
        if url_final:
            print(f"¡Conexión exitosa! Enlace extraído mediante: {proxy}")
            return url_final
            
    print("Error: Todos los proxies de México en la lista fallaron o están bloqueados por OK.ru en este ciclo.")
    return None

def actualizar_archivo_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo '{ARCHIVO_M3U}' no se encuentra en la raíz.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    ip_autorizada = "127.0.0.1"
    match_ip = re.search(r'/srcIp/([^/]+)/', nueva_url)
    if match_ip:
        ip_autorizada = match_ip.group(1)
        print(f"IP autorizada para streaming: {ip_autorizada}")

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
    print("Lista M3U actualizada con éxito.")

if __name__ == "__main__":
    url_final = obtener_m3u8()
    if url_final:
        actualizar_archivo_m3u(url_final)
