import os
import subprocess
import re

# Configuración de variables
URL_OK_RU = "https://ok.ru/videoembed/10849691639514?nochat=1&autoplay=1"
ARCHIVO_M3U = "XOY"

def obtener_m3u8():
    try:
        # Se añade un User-Agent de navegador para evitar bloqueos de OK.ru
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        print("Intentando extraer la URL con Streamlink...")
        resultado = subprocess.run(
            [
                "streamlink", 
                URL_OK_RU, 
                "best", 
                "--stream-url",
                f"--http-header=User-Agent={user_agent}"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        url_extraida = resultado.stdout.strip()
        if ".m3u8" in url_extraida:
            print(f"¡Éxito! URL extraída: {url_extraida}")
            return url_extraida
        else:
            print("Streamlink respondió, pero no devolvió un enlace .m3u8 válido.")
            return None
            
    except subprocess.CalledProcessError as e:
        # Captura el error específico de Streamlink sin romper el script completo
        print("\n[AVISO] Streamlink no pudo obtener la señal.")
        print("Esto ocurre usualmente si el canal está OFFLINE (fuera del aire) en este momento.")
        print(f"Detalle técnico: {e.stderr.strip()}\n")
        return None
    except Exception as e:
        print(f"Error inesperado: {e}")
        return None

def actualizar_archivo_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo '{ARCHIVO_M3U}' no existe en la raíz del repositorio.")
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
        print("Estructura localizada en XOY. URL actualizada correctamente.")
    else:
        print("No se encontró el bloque exacto en XOY. Añadiendo canal al final del archivo.")
        nuevo_contenido = contenido.rstrip() + f"\n\n{parametros_fijos}\n{nueva_url}\n"

    with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
        f.write(nuevo_contenido)
    print("Cambios guardados con éxito.")

if __name__ == "__main__":
    url_m3u8 = obtener_m3u8()
    if url_m3u8:
        max_intentos = actualizar_archivo_m3u(url_m3u8)
    else:
        print("No se modificó el archivo 'XOY' porque no hay transmisión activa.")
