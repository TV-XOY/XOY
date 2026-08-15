import os
import subprocess
import re
import json

URL_OK_RU = "https://ok.ru/videoembed/10849691639514?nochat=1&autoplay=1"
ARCHIVO_M3U = "XOY"

def obtener_m3u8():
    proxy_tor = "socks5://127.0.0.1:9050"
    
    # Intentos secuenciales: 
    # 1. Comando tolerante con Tor limitando altura en la petición
    # 2. Comando Tor sin filtros de calidad (extracción limpia y filtrado manual posterior)
    # 3. Intento directo sin Proxy por si Tor está completamente bloqueado
    estrategias = [
        {"name": "Tor + Filtro Directo 480p", "args": ["-f", "best[height<=480]/bestvideo[height<=480]+bestaudio", "--proxy", proxy_tor]},
        {"name": "Tor + Extracción Completa", "args": ["--proxy", proxy_tor]},
        {"name": "Conexión Directa GitHub (Sin Tor)", "args": []}
    ]
    
    for estrategia in estrategias:
        try:
            print(f"Probando estrategia: {estrategia['name']}...")
            
            comando = [
                "yt-dlp",
                URL_OK_RU,
                "--dump-json",
                "--no-warnings",
                "--no-check-certificates",
                "--impersonate", "chrome",  
                "--extractor-args", "okru:player_type=modern"
            ] + estrategia["args"]
            
            resultado = subprocess.run(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=90
            )
            
            datos_video = json.loads(resultado.stdout)
            formats = datos_video.get("formats", [])
            
            # --- Lógica de filtrado manual para forzar 480p ("medium") ---
            # Buscamos en reversa (de menor a mayor calidad usualmente)
            for f in reversed(formats):
                url_f = f.get("url", "")
                height = f.get("height", 0)
                
                # Si cumple con ser HLS (.m3u8) y es calidad media/480p
                if ".m3u8" in url_f:
                    if height == 480 or "_medium" in url_f:
                        print(f"¡Éxito! Calidad 480p/Medium localizada mediante {estrategia['name']}.")
                        return url_f

            # Si el filtro manual no halló el string exacto pero hay una URL procesada válida
            url_base = datos_video.get("url")
            if url_base and ".m3u8" in url_base:
                # Modificación dinámica de la URL master si es posible
                if "10454955395802_highest" in url_base:
                    url_base = url_base.replace("_highest", "_medium")
                    print("Calidad adaptada dinámicamente de highest a medium.")
                return url_base
                
        except Exception as e:
            print(f"Fallo en {estrategia['name']}: Nodo Tor bloqueado o error de formato. Reintentando...")
            continue
            
    return None

def actualizar_archivo_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo '{ARCHIVO_M3U}' no se encuentra en la raíz.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    # Extraemos la IP autorizada de la URL de OK.ru
    ip_autorizada = "190.103.179.98"
    match_ip = re.search(r'/srcIp/([^/]+)/', nueva_url)
    if match_ip:
        ip_autorizada = match_ip.group(1)
        print(f"IP de extracción vinculada: {ip_autorizada}")

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
        print("¡M3U Actualizado! Bloque reemplazado protegiendo tu lista.")
    else:
        print("Canal nuevo. Añadiendo al final de XOY de forma segura.")
        lineas_finales = lineas + ['\n'] + bloque_nuevo

    with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
        f.writelines(lineas_finales)
    print("Cambios guardados exitosamente.")

if __name__ == "__main__":
    url_m3u8 = obtener_m3u8()
    if url_m3u8:
        actualizar_archivo_m3u(url_m3u8)
    else:
        print("No se pudo obtener una URL válida debido a bloqueos estrictos de OK.ru.")
