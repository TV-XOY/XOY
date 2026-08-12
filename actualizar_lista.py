import os
import subprocess
import re
import json

URL_OK_RU = "https://ok.ru/videoembed/10849691639514?nochat=1&autoplay=1"
ARCHIVO_M3U = "XOY"

def obtener_m3u8():
    try:
        print("Iniciando extracción con yt-dlp...")
        
        # Comando avanzado para extraer metadatos simulando un navegador Chrome real
        comando = [
            "yt-dlp",
            URL_OK_RU,
            "--dump-json",
            "--no-warnings",
            "--impersonate", "chrome",  # Hace que la huella TLS sea idéntica a la de Chrome para saltar bloqueos de bots
            "--extractor-args", "okru:player_type=modern"
        ]
        
        resultado = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        # Parseamos el JSON devuelto por yt-dlp
        datos_video = json.loads(resultado.stdout)
        
        # Buscamos la URL con formato m3u8 (HLS) de mejor calidad
        url_extraida = datos_video.get("url")
        
        if url_extraida and ".m3u8" in url_extraida:
            print(f"¡Éxito Absoluto! URL encontrada de forma nativa: {url_extraida}")
            return url_extraida
        
        # Fallback por si la URL principal no es m3u8
        formats = datos_video.get("formats", [])
        for f in reversed(formats): # Revisamos de mejor a menor calidad
            url_formato = f.get("url", "")
            if ".m3u8" in url_formato:
                print(f"¡Éxito Absoluto! URL encontrada en formatos: {url_formato}")
                return url_formato
                
        print("yt-dlp leyó la página pero no se localizó ningún enlace .m3u8.")
        return None
            
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] yt-dlp no pudo procesar la página de OK.ru.")
        print(f"Detalle técnico de la consola: {e.stderr.strip()}\n")
        return None
    except Exception as e:
        print(f"Error inesperado en el script: {e}")
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
        print("No se modificó el archivo debido a las restricciones de la plataforma.")
