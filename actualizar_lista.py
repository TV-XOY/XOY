import os
import subprocess
import re
import json
import urllib.request

URL_OK_RU = "https://ok.ru/videoembed/10849691639514?nochat=1&autoplay=1"
ARCHIVO_M3U = "XOY"

def obtener_lista_proxies_mexico():
    """Descarga una lista fresca y gratuita de proxies de México usando la API de ProxyScrape."""
    print("Descargando lista actualizada de proxies gratuitos de México...")
    url_api = "https://proxyscrape.com"
    try:
        req = urllib.request.Request(url_api, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            contenido = response.read().decode('utf-8')
            # Limpiamos el texto y extraemos las IPs con su puerto
            proxies = [linea.strip() for linea in contenido.splitlines() if linea.strip()]
            print(f"Se encontraron {len(proxies)} proxies de México disponibles.")
            return proxies
    except Exception as e:
        print(f"Error al descargar la lista pública de proxies: {e}")
        return []

def obtener_m3u8():
    # Obtenemos la lista dinámica de IPs mexicanas
    lista_proxies = obtener_lista_proxies_mexico()
    
    # Si la lista pública falla, dejamos una lista de respaldo manual (IP:Puerto de México)
    if not lista_proxies:
        print("Usando lista de proxies de respaldo...")
        lista_proxies = ["201.159.97.25:8081", "148.230.4.146:999", "138.186.201.133:8082"]

    for proxy in lista_proxies:
        proxy_url = f"http://{proxy}"
        print(f"\nProbando extracción a 480p con el proxy: {proxy}...")
        
        try:
            comando = [
                "yt-dlp",
                URL_OK_RU,
                "-f", "best[height<=480]/bestvideo[height<=480]+bestaudio",
                "--dump-json",
                "--no-warnings",
                "--no-check-certificates",
                "--impersonate", "chrome",  
                "--proxy", proxy_url,
                "--extractor-args", "okru:player_type=modern"
            ]
            
            resultado = subprocess.run(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=45  # Tiempo límite corto para descartar proxies lentos rápido
            )
            
            datos_video = json.loads(resultado.stdout)
            formats = datos_video.get("formats", [])
            
            # 1. Buscador manual en la lista de formatos devueltos por el proxy
            for f in reversed(formats):
                url_f = f.get("url", "")
                height = f.get("height", 0)
                if ".m3u8" in url_f:
                    if height == 480 or "_medium" in url_f:
                        print(f"¡Éxito total! Enlace 480p/Medium obtenido con el proxy {proxy}")
                        return url_f
            
            # 2. Forzado dinámico si el enlace master está disponible en alta resolución
            url_base = datos_video.get("url")
            if url_base and ".m3u8" in url_base:
                if "_highest" in url_base:
                    url_base = url_base.replace("_highest", "_medium")
                    print("URL Master adaptada internamente a formato estable (480p/Medium).")
                return url_base
                
        except Exception:
            print(f"El proxy {proxy} falló, fue bloqueado o es demasiado lento. Probando el siguiente...")
            continue
            
    return None

def actualizar_archivo_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo '{ARCHIVO_M3U}' no se encuentra en la raíz.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    ip_autorizada = "190.103.179.98"
    match_ip = re.search(r'/srcIp/([^/]+)/', nueva_url)
    if match_ip:
        ip_autorizada = match_ip.group(1)
        print(f"IP Mexicana inyectada en las cabeceras: {ip_autorizada}")

    bloque_nuevo = [
        '#EXTINF:-1 tvg-name="CANAL13.mx" tvg-chno="13" tvg-id="CANAL13.mx" tvg-logo="https://canal13mexico.com" group-title="NACIONALES",CANAL 13 MERIDA (480p)\n',
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
        print("¡Lista M3U actualizada de forma segura!")
    else:
        lineas_finales = lineas + ['\n'] + bloque_nuevo

    with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
        f.writelines(lineas_finales)
    print("Cambios guardados exitosamente.")

if __name__ == "__main__":
    url_m3u8 = obtener_m3u8()
    if url_m3u8:
        actualizar_archivo_m3u(url_m3u8)
    else:
        print("No se pudo obtener el enlace; todos los proxies de la lista pública fallaron en esta vuelta.")
