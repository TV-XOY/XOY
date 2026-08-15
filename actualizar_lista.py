import os
import subprocess
import re
import json
import time
import socket

URL_OK_RU = "https://ok.ru/videoembed/10849691639514?nochat=1&autoplay=1"
ARCHIVO_M3U = "XOY"

def cambiar_identidad_tor():
    """Envía una señal al puerto de control de Tor para forzar un cambio de nodo mexicano."""
    try:
        print("Solicitando cambio de nodo Tor (buscando otra IP de México)...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", 9051))
        s.send(b'AUTHENTICATE ""\r\n')
        respuesta = s.recv(1024)
        if b"250" in respuesta:
            s.send(b'SIGNAL NEWNYM\r\n')
            respuesta2 = s.recv(1024)
            if b"250" in respuesta2:
                print("Señal de nueva identidad enviada con éxito.")
        s.close()
        time.sleep(8) # Esperamos a que el circuito se estabilice
    except Exception as e:
        print(f"No se pudo contactar con el puerto de control de Tor: {e}")

def obtener_m3u8():
    proxy_tor = "socks5://127.0.0.1:9050"
    intentos_maximos = 5
    
    for intento in range(1, intentos_maximos + 1):
        print(f"\n--- Intento {intento} de {intentos_maximos} usando Tor (México) ---")
        try:
            # Comando optimizado para extraer el formato 480p directo
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
                timeout=70
            )
            
            datos_video = json.loads(resultado.stdout)
            formats = datos_video.get("formats", [])
            
            # 1. Buscador manual de calidad en los formatos devueltos
            for f in reversed(formats):
                url_f = f.get("url", "")
                height = f.get("height", 0)
                if ".m3u8" in url_f:
                    if height == 480 or "_medium" in url_f:
                        print(f"¡Éxito en intento {intento}! Enlace 480p/Medium obtenido correctamente.")
                        return url_f
            
            # 2. Forzado dinámico si yt-dlp entrega la master link en alta definición
            url_base = datos_video.get("url")
            if url_base and ".m3u8" in url_base:
                if "_highest" in url_base:
                    url_base = url_base.replace("_highest", "_medium")
                    print("URL Master adaptada internamente a formato estable (480p).")
                return url_base
                
        except Exception as e:
            print(f"El intento {intento} falló o el nodo mexicano actual está caído.")
            # Si no es el último intento, rotamos la IP de Tor para probar con otro nodo de México
            if intento < intentos_maximos:
                cambiar_identidad_tor()
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
        print(f"IP Mexicana vinculada al Token: {ip_autorizada}")

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
        print("¡Lista XOY actualizada con éxito a 480p!")
    else:
        lineas_finales = lineas + ['\n'] + bloque_nuevo

    with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
        f.writelines(lineas_finales)

if __name__ == "__main__":
    url_m3u8 = obtener_m3u8()
    if url_m3u8:
        actualizar_archivo_m3u(url_m3u8)
    else:
        print("No se pudo extraer la URL; la red Tor no ofreció nodos mexicanos estables en esta vuelta.")
