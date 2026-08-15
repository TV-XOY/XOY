import os
import subprocess
import re
import json

URL_OK_RU = "https://ok.ru/videoembed/10849691639514?nochat=1&autoplay=1"
ARCHIVO_M3U = "XOY"

def obtener_m3u8():
    try:
        print("Iniciando extracción a 480p a través de la Red Tor (México)...")
        proxy_tor = "socks5://127.0.0.1:9050"
        
        # Modificamos el comando para pedir específicamente calidad 480p
        # Usamos format selector: bestvideo[height<=]+bestaudio/best[height<=]
        comando = [
            "yt-dlp",
            URL_OK_RU,
            "-f", "best[height<=][ext=mp]/best[height<=]", # Prioriza 480p estable
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
        
        # Intentamos obtener la URL del formato seleccionado por yt-dlp
        url_extraida = datos_video.get("url")
        
        # Si yt-dlp no devolvió una m3u8 directa en el campo principal, buscamos en los formatos
        if not url_extraida or ".m3u8" not in url_extraida:
            formats = datos_video.get("formats",)
            # Buscamos de forma inversa el mejor formato que cumpla con ser m3u8 y <= 480p
            for f in reversed(formats):
                height = f.get("height", 0)
                url_formato = f.get("url", "")
                if ".m3u8" in url_formato and height <= 480:
                    print(f"Calidad encontrada: {height}p")
                    return url_formato
        
        return url_extraida if url_extraida and ".m3u8" in url_extraida else None
            
    except Exception as e:
        print(f"Error al extraer: {e}")
        return None

def actualizar_archivo_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo '{ARCHIVO_M3U}' no se encuentra en la raíz.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    # Extraemos de forma dinámica la IP que usó Tor
    ip_autorizada = "190.103.179.98"
    match_ip = re.search(r'/srcIp/([^/]+)/', nueva_url)
    if match_ip:
        ip_autorizada = match_ip.group(1)
        print(f"IP detectada para 480p: {ip_autorizada}")

    bloque_nuevo = [
        '#EXTINF:-1 tvg-name="CANAL13.mx" tvg-chno="13" tvg-id="CANAL13.mx" tvg-logo="https://canal13mexico.com/wp-content/uploads/2024/04/cropped-LOGO-CANAL-TRECE.png" group-title="NACIONALES",CANAL 13 MERIDA\n',
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
        lineas_finales = lineas[:indice_inicio] + bloque_nuevo + lineas[indice_fin + :]
        print("¡Éxito! Se actualizó el canal a calidad 480p.")
    else:
        print("Añadiendo nuevo canal 480p al final.")
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
        print("No se pudo obtener la URL en 480p.")
