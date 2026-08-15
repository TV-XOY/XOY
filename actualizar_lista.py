import os
import subprocess
import re
import json

URL_OK_RU = "https://ok.ru/videoembed/10849691639514?nochat=1&autoplay=1"
ARCHIVO_M3U = "XOY"

def obtener_m3u8():
    try:
        print("Iniciando extracción a través de la Red Tor (Túnel Exclusivo México)...")
        proxy_tor = "socks5://127.0.0.1:9050"
        
        # Pedimos el mejor formato que sea menor o igual a 480p
        comando = [
            "yt-dlp",
            URL_OK_RU,
            "-f", "best[height<=480]/bestvideo[height<=480]+bestaudio",
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
            timeout=120
        )
        
        datos_video = json.loads(resultado.stdout)
        formats = datos_video.get("formats", [])
        
        # 1. Buscamos manualmente en los formatos disponibles si hay un link directo a "medium"
        for f in reversed(formats):
            url_f = f.get("url", "")
            height = f.get("height", 0)
            if ".m3u8" in url_f:
                if height == 480 or "_medium" in url_f:
                    print(f"¡Éxito! Calidad 480p/Medium localizada con IP de México.")
                    return url_f
        
        # 2. Si yt-dlp nos da una URL genérica alta, reescribimos el token a versión 'medium'
        url_extraida = datos_video.get("url")
        if url_extraida and ".m3u8" in url_extraida:
            if "_highest" in url_extraida:
                url_extraida = url_extraida.replace("_highest", "_medium")
                print("Calidad de video forzada dinámicamente a 480p (Medium).")
            return url_extraida
        
        return None
            
    except Exception as e:
        print(f"Error al extraer: {e}")
        return None

def actualizar_archivo_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo '{ARCHIVO_M3U}' no se encuentra en la raíz.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    # Buscamos la IP mexicana que nos asignó Tor para mandarla en la cabecera
    ip_autorizada = "190.103.179.98"
    match_ip = re.search(r'/srcIp/([^/]+)/', nueva_url)
    if match_ip:
        ip_autorizada = match_ip.group(1)
        print(f"IP Mexicana Autorizada: {ip_autorizada}")

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
        # Se solucionan los problemas previos de cortes en la lista
        lineas_finales = lineas[:indice_inicio] + bloque_nuevo + lineas[indice_fin + 1:]
        print("¡M3U Actualizado! Bloque de Canal 13 Mérida reemplazado con éxito.")
    else:
        print("Canal nuevo detectado. Añadiendo al final de la lista XOY de forma segura.")
        lineas_finales = lineas + ['\n'] + bloque_nuevo

    with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
        f.writelines(lineas_finales)
    print("Cambios guardados exitosamente.")

if __name__ == "__main__":
    url_m3u8 = obtener_m3u8()
    if url_m3u8:
        actualizar_archivo_m3u(url_m3u8)
    else:
        print("No se modificó el archivo debido a las restricciones de la conexión.")
