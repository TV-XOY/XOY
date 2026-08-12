import os
import subprocess
import re
import urllib.request

URL_OK_RU = "https://ok.ru/live/10849691639514"
ARCHIVO_M3U = "XOY"

def obtener_proxy_mexico():
    """Busca una lista de proxies públicos e intenta extraer uno de México o LATAM"""
    try:
        print("Obteniendo lista de proxies públicos...")
        url = "https://proxyscrape.com"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            proxies = response.read().decode('utf-8').strip().split('\n')
            if proxies and len(proxies[0]) > 5:
                proxy_valido = proxies[0].strip()
                print(f"Proxy de México encontrado: http://{proxy_valido}")
                return f"http://{proxy_valido}"
    except Exception as e:
        print(f"No se pudo obtener proxy específico de México: {e}")
    
    # Fallback: Si falla el de México, intenta uno global rápido
    print("Usando proxy alternativo global...")
    return "http://45.70.198.81:8080" # Proxy LATAM genérico de respaldo

def obtener_m3u8():
    proxy = obtener_proxy_mexico()
    user_agent = (
        "Mozilla/5.0 (Linux; Android 10; Mi 9T) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    )
    
    try:
        print("Intentando extraer la URL con Streamlink a través del Proxy...")
        
        # Comando estructurado con Proxy y User Agent móviles para romper el bloqueo regional
        comando = [
            "streamlink", 
            URL_OK_RU, 
            "best", 
            "--stream-url",
            f"--http-header=User-Agent={user_agent}",
            f"--http-proxy={proxy}"
        ]
        
        resultado = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            timeout=25 # Evita que GitHub se quede congelado si el proxy es lento
        )
        
        url_extraida = resultado.stdout.strip()
        if ".m3u8" in url_extraida:
            print(f"¡Éxito Absoluto! URL extraída: {url_extraida}")
            return url_extraida
        else:
            print("Streamlink no devolvió un enlace .m3u8 válido.")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Streamlink falló usando el proxy {proxy}.")
        print(f"Detalle técnico de la plataforma: {e.stderr.strip()}\n")
        return None
    except subprocess.TimeoutExpired:
        print("\n[ERROR] El proxy asignado tardó demasiado en responder (Timeout).\n")
        return None
    except Exception as e:
        print(f"Error inesperado: {e}")
        return None

def actualizar_archivo_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo '{ARCHIVO_M3U}' no existe.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        contenido = f.read()

    parametros_fijos = (
        '#EXTINF:-1 tvg-name="CANAL13.mx" tvg-chno="13" tvg-id="CANAL13.mx" '
        'tvg-logo="https://canal13mexico.com" '
        'group-title="NACIONALES",CANAL 13 MERIDA\n'
        '#EXTVLCOPT:network-caching=2000\n'
        '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Mobile Safari/537.36\n'
        '#EXTVLCOPT--http-reconnect=true\n'
        '#KODIPROP:inputstream.adaptive.manifest_type=hls'
    )

    patron = r'(#EXTINF:-1.*?CANAL 13 MERIDA\n.*?(?:#EXTVLCOPT.*?)\n(?:#KODIPROP.*?)\n)(https?://[^\s]+)'
    
    if re.search(patron, contenido):
        nuevo_contenido = re.sub(patron, f"\\1{nueva_url}", contenido)
        print("Estructura localizada. URL actualizada correctamente en el bloque.")
    else:
        print("No se encontró el bloque exacto. Añadiendo canal al final del archivo.")
        nuevo_contenido = contenido.rstrip() + f"\n\n{parametros_fijos}\n{nueva_url}\n"

    with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
        f.write(nuevo_contenido)
    print("Cambios guardados con éxito en el archivo XOY.")

if __name__ == "__main__":
    url_m3u8 = obtener_m3u8()
    if url_m3u8:
        actualizar_archivo_m3u(url_m3u8)
    else:
        print("No se modificó el archivo porque falló la evasión del bloqueo regional.")
