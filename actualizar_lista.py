import os
import subprocess
import re
import json

URL_OK_RU = "https://ok.ru/videoembed/10849691639514?nochat=1&autoplay=1"
ARCHIVO_M3U = "XOY"

def obtener_m3u8():
    try:
        # Extraer credenciales de Secrets (Variables de entorno en el .yml)
        user = os.environ.get("PROXY_USER")
        pw = os.environ.get("PROXY_PASS")
        host = os.environ.get("PROXY_HOST")
        port = os.environ.get("PROXY_PORT")

        # Formato de proxy con autenticación: protocolo://usuario:contraseña@host:puerto
        proxy_url = f"http://{user}:{pw}@{host}:{port}"
        
        print(f"Iniciando extracción con Proxy México: {host}")
        
        comando = [
            "yt-dlp",
            URL_OK_RU,
            "-f", "best[height<=]", # Calidad estable de 480p según tu preferencia
            "--dump-json",
            "--no-warnings",
            "--impersonate", "chrome",
            "--proxy", proxy_url,
            "--extractor-args", "okru:player_type=modern"
        ]
        
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        datos_video = json.loads(resultado.stdout)
        
        # BUSQUEDA FLEXIBLE: Buscamos ".m3u8" en cualquier parte de la URL
        url_directa = datos_video.get("url", "")
        if ".m3u8" in url_directa:
            return url_directa
            
        # Si no está en la principal, buscamos en la lista de formatos
        formats = datos_video.get("formats",)
        for f in reversed(formats):
            url_f = f.get("url", "")
            if ".m3u8" in url_f:
                return url_f
        
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def actualizar_archivo_m3u(nueva_url):
    # La lógica de actualización de tu archivo 'XOY' se mantiene igual
    # (Asegúrate de usar la variable 'nueva_url' obtenida)
    pass 

if __name__ == "__main__":
    url_final = obtener_m3u8()
    if url_final:
        print(f"URL detectada correctamente")
        actualizar_archivo_m3u(url_final)
