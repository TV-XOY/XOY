import os
import subprocess
import re
import json
import urllib.request

URL_OK_RU = "https://ok.ru/videoembed/10849691639514?nochat=1&autoplay=1"
ARCHIVO_M3U = "XOY"

def obtener_lista_proxies_mexico():
    """Obtiene proxies globales en texto plano de fuentes estables y filtra IPs con formato correcto"""
    print("Obteniendo lista de proxies crudos desde repositorios estables...")
    proxies_encontrados = set()
    
    # Fuentes abiertas en texto plano actualizadas cada hora que no bloquean GitHub Actions
    urls_fuentes = [
        "https://githubusercontent.com",
        "https://githubusercontent.com",
        "https://githubusercontent.com"
    ]
    
    # Expresión regular que obliga a que la línea contenga estrictamente IP:PUERTO (ej: 189.240.75.10:8080)
    # Ignora cualquier JSON, HTML, corchetes o texto.
    regex_ip_port = re.compile(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})$')

    for url in urls_fuentes:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=10) as response:
                contenido = response.read().decode('utf-8', errors='ignore')
                
                for linea in contenido.split('\n'):
                    linea_limpia = linea.strip()
                    
                    # Si la línea contiene espacios u otros datos (como el país), extraemos solo la IP:PUERTO
                    match = regex_ip_port.search(linea_limpia)
                    if match:
                        proxies_encontrados.add(match.group(0))
                    else:
                        # Intenta buscar una IP:PUERTO en cualquier parte de la línea si no está limpia
                        match_libre = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}', linea_limpia)
                        if match_libre:
                            proxies_encontrados.add(match_libre.group(0))
                            
        except Exception as e:
            continue

    lista_final = list(proxies_encontrados)
    print(f"Filtrado estricto completado. Se detectaron {len(lista_final)} IPs reales y limpias para probar.")
    return lista_final

def extraer_con_proxy(proxy_ip_port):
    """Intenta extraer el m3u8 usando un proxy de la lista"""
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
        "--socket-timeout", "10", # Timeout rápido para descartar IPs muertas en segundos
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
        print("Error: No se pudieron obtener IPs de las fuentes.")
        return None

    # Limitamos a un máximo de 80 proxies por ejecución para no congelar el flujo de GitHub
    max_intentos = min(len(lista_proxies), 80)
    
    for i in range(max_intentos):
        proxy = lista_proxies[i]
        print(f"[{i+1}/{max_intentos}] Evaluando proxy limpio: {proxy}...")
        url_final = extraer_con_proxy(proxy)
        if url_final:
            print(f"¡Éxito! Enlace extraído correctamente usando: {proxy}")
            return url_final
            
    print("Error: Ninguno de los proxies probados en esta ronda logró saltar el bloqueo de OK.ru.")
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
        print(f"IP de streaming detectada: {ip_autorizada}")

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
