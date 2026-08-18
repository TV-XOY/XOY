import os
import subprocess
import re
import json
import urllib.request

URL_OK_RU = "https://ok.ru/videoembed/10849691639514?nochat=1&autoplay=1"
ARCHIVO_M3U = "XOY"

def obtener_lista_proxies_globales():
    """Descarga proxies crudos de fuentes abiertas masivas y extrae solo combinaciones IP:Puerto válidas"""
    print("Iniciando escaneo de servidores espejo de proxies...")
    proxies_encontrados = set()
    
    # Fuentes globales de proxies HTTP en vivo (Monosans y Free-Proxy-List)
    urls_fuentes = [
        "https://free-proxy-list.net/"
    ]
    
    for url in urls_fuentes:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            with urllib.request.urlopen(req, timeout=12) as response:
                contenido = response.read().decode('utf-8', errors='ignore')
                
                # Expresión regular permisiva: Encuentra cualquier formato IP:PUERTO dentro de textos o tablas HTML
                matches = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}\b', contenido)
                for match in matches:
                    proxies_encontrados.add(match)
        except Exception as e:
            print(f"Aviso: Ocurrió un inconveniente temporal con una fuente ({e})")
            continue

    lista_final = list(proxies_encontrados)
    print(f"Búsqueda finalizada. Se detectaron {len(lista_final)} direcciones IP listas para testing.")
    return lista_final

def extraer_con_proxy(proxy_ip_port):
    """Intenta extraer el streaming m3u8 a través del proxy seleccionado"""
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
        "--socket-timeout", "10", # Tiempo bajo para saltar rápido proxies caídos o lentos
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
    lista_proxies = obtener_lista_proxies_globales()
    if not lista_proxies:
        print("Error: No se lograron obtener IPs de respaldo.")
        return None

    # Limitamos la prueba a las primeras 90 IPs para asegurar estabilidad dentro del tiempo límite de GitHub
    max_intentos = min(len(lista_proxies), 90)
    print(f"Iniciando escaneo secuencial. Evaluando un espectro de {max_intentos} servidores...")
    
    for i in range(max_intentos):
        proxy = lista_proxies[i]
        print(f"[{i+1}/{max_intentos}] Evaluando túnel: {proxy}")
        url_final = extraer_con_proxy(proxy)
        if url_final:
            print(f"¡Éxito absoluto! Enlace extraído correctamente con la IP: {proxy}")
            return url_final
            
    print("Error: Los servidores testeados en esta ronda se encuentran congestionados o rechazados por la plataforma de origen.")
    return None

def actualizar_archivo_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo objetivo '{ARCHIVO_M3U}' no está en el repositorio.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    ip_autorizada = "127.0.0.1"
    match_ip = re.search(r'/srcIp/([^/]+)/', nueva_url)
    if match_ip:
        ip_autorizada = match_ip.group(1)
        print(f"IP de streaming localizada: {ip_autorizada}")

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
