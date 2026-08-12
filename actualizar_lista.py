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

    # Extraemos la IP exacta que usó Tor
    ip_autorizada = "190.103.179.98"
    match_ip = re.search(r'/srcIp/([^/]+)/', nueva_url)
    if match_ip:
        ip_autorizada = match_ip.group(1)
        print(f"IP de extracción detectada y autorizada: {ip_autorizada}")

    # Estructura limpia que SÍ te funcionó para reproducir
    parametros_fijos = (
        '#EXTINF:-1 tvg-name="CANAL13.mx" tvg-chno="13" tvg-id="CANAL13.mx" '
        'tvg-logo="https://canal13mexico.com/wp-content/uploads/2024/04/cropped-LOGO-CANAL-TRECE.png" '
        'group-title="NACIONALES",CANAL 13 MERIDA\n'
        '#EXTVLCOPT:network-caching=2000\n'
        f'#EXTVLCOPT:http-x-forwarded-for={ip_autorizada}\n'
        '#EXTVLCOPT--http-reconnect=true\n'
        '#KODIPROP:inputstream.adaptive.manifest_type=hls\n'
        f'#KODIPROP:inputstream.adaptive.stream_headers=User-Agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36&X-Forwarded-For={ip_autorizada}'
    )

    # NUEVO BUSCADOR RADICAL: Busca desde el inicio del #EXTINF de CANAL 13 MERIDA 
    # hasta encontrar la siguiente URL (http...index.m3u8), sin importar qué haya en medio.
    patron_radical = r'(#EXTINF:-1[^#\n]*?CANAL 13 MERIDA.*?\n)(?:#EXTVLCOPT.*?\n|#KODIPROP.*?\n|https?://.*?\n)*(https?://[^\s]+)'
    
    if re.search(patron_radical, contenido, re.DOTALL):
        # Si encuentra cualquier bloque viejo o duplicado que diga CANAL 13 MERIDA, lo sobrescribe por completo
        nuevo_contenido = re.sub(patron_radical, f"{parametros_fijos}\n{nueva_url}", contenido, flags=re.DOTALL)
        print("¡Éxito! Bloque previo localizado. Se reemplazó la URL vieja de forma limpia.")
    else:
        # Solo si borraste el canal por completo, lo añadirá al final por primera vez
        print("Bloque previo no detectado. Añadiendo canal de forma limpia al final.")
        nuevo_contenido = contenido.rstrip() + f"\n\n{parametros_fijos}\n{nueva_url}\n"

    with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
        f.write(nuevo_contenido)
    print("Cambios guardados con éxito en el archivo XOY.")

if __name__ == "__main__":
    url_m3u8 = obtener_m3u8()
    if url_m3u8:
        print(f"URL obtenida: {url_m3u8}")
        actualizar_archivo_m3u(url_m3u8)
    else:
        print("No se modificó el archivo debido a las restricciones de la conexión.")
