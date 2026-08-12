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
        contenido = f.read()

    # Extraemos de la URL la IP exacta que usó Tor para generar el token de OK.ru
    ip_autorizada = "190.103.179.98" # IP de respaldo por si falla la extracción
    match_ip = re.search(r'/srcIp/([^/]+)/', nueva_url)
    if match_ip:
        ip_autorizada = match_ip.group(1)
        print(f"IP de extracción detectada y autorizada: {ip_autorizada}")

    # Modificamos los parámetros fijos e inyectamos la directiva http-x-forwarded-for con la IP del token.
    # También fijamos el User-Agent para que coincida con el validador de OK.ru.
    parametros_fijos = (
        f'#EXTINF:-1 tvg-name="CANAL13.mx" tvg-chno="13" tvg-id="CANAL13.mx" '
        f'tvg-logo="https://canal13mexico.com" '
        f'group-title="NACIONALES",CANAL 13 MERIDA\n'
        f'#EXTVLCOPT:network-caching=2000\n'
        f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\n'
        f'#EXTVLCOPT:http-x-forwarded-for={ip_autorizada}\n'
        f'#EXTVLCOPT--http-reconnect=true\n'
        f'#KODIPROP:inputstream.adaptive.manifest_type=hls\n'
        f'#KODIPROP:inputstream.adaptive.stream_headers=User-Agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36&X-Forwarded-For={ip_autorizada}'
    )

    # Buscamos si ya existía el bloque (corregido para que identifique tanto el formato viejo como el nuevo)
    patron = r'(#EXTINF:-1.*?CANAL 13 MERIDA\n.*?)(https?://[^\s]+)'
    
    if re.search(patron, contenido):
        # Si ya existe el canal en el archivo, reemplaza todo el bloque de parámetros y la URL vieja
        nuevo_contenido = re.sub(patron, f"{parametros_fijos}\n{nueva_url}", contenido)
        print("Estructura localizada. Canal 13 Mérida actualizado con éxito.")
    else:
        # Si es la primera vez o no se encuentra el formato exacto, lo añade al final
        print("Bloque previo no detectado. Añadiendo canal al final de XOY.")
        nuevo_contenido = contenido.rstrip() + f"\n\n{parametros_fijos}\n{nueva_url}\n"

    with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
        f.write(nuevo_contenido)
    print("Cambios guardados con éxito.")

if __name__ == "__main__":
    url_m3u8 = obtener_m3u8()
    if url_m3u8:
        print(f"¡Éxito Absoluto! URL obtenida: {url_m3u8}")
        actualizar_archivo_m3u(url_m3u8)
    else:
        print("No se modificó el archivo debido a las restricciones de la conexión.")
