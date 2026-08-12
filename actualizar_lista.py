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
            
    except Exception as e:
        print(f"Error al extraer: {e}")
        return None

def actualizar_archivo_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo '{ARCHIVO_M3U}' no se encuentra en la raíz.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    # Extraemos de forma dinámica la IP que usó Tor en esta vuelta
    ip_autorizada = "190.103.179.98"
    match_ip = re.search(r'/srcIp/([^/]+)/', nueva_url)
    if match_ip:
        ip_autorizada = match_ip.group(1)
        print(f"IP de extracción detectada automáticamente: {ip_autorizada}")

    # Bloque limpio con las cabeceras que te funcionaron
    bloque_nuevo = [
        '#EXTINF:-1 tvg-name="CANAL13.mx" tvg-chno="13" tvg-id="CANAL13.mx" tvg-logo="https://canal13mexico.com/wp-content/uploads/2024/04/cropped-LOGO-CANAL-TRECE.png" group-title="NACIONALES",CANAL 13 MERIDA\n',
        '#EXTVLCOPT:network-caching=2000\n',
         f'#EXTVLCOPT:http-x-forwarded-for={ip_autorizada}\n',
        '#EXTVLCOPT--http-reconnect=true\n',
        '#KODIPROP:inputstream.adaptive.manifest_type=hls\n',
        f'#KODIPROP:inputstream.adaptive.stream_headers=User-Agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36&X-Forwarded-For={ip_autorizada}\n',
        f'{nueva_url}\n'
    ]

    indice_inicio = -1
    indice_fin = -1

    # Buscamos la línea exacta donde está el Canal 13 Mérida
    for i, linea in enumerate(lineas):
        if "CANAL 13 MERIDA" in linea and "#EXTINF" in linea:
            indice_inicio = i
            break

    if indice_inicio != -1:
        # Si lo encuentra, buscamos dónde termina su bloque (la línea de la URL http...)
        for j in range(indice_inicio + 1, len(lineas)):
            if lineas[j].startswith("http://") or lineas[j].startswith("https://"):
                indice_fin = j
                break
            # Si topa con otro canal antes de una URL (por error de formato anterior), frena ahí
            if lineas[j].startswith("#EXTINF"):
                indice_fin = j - 1
                break

    if indice_inicio != -1 and indice_fin != -1:
        # Reemplaza UNICAMENTE el rango del Canal 13 sin tocar lo que está antes ni después
        lineas_finales = lineas[:indice_inicio] + bloque_nuevo + lineas[indice_fin + 1:]
        print("¡Éxito! Bloque previo localizado. Se reemplazó la URL vieja protegiendo el resto de canales.")
    else:
        # Si es un archivo nuevo o borraste el canal, lo añade limpiamente al final sin romper nada
        print("Canal no encontrado previamente. Añadiendo al final de la lista XOY de forma segura.")
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
        print("No se modificó el archivo debido a las restricciones de la conexión.")
