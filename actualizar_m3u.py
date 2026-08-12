import os
import subprocess

# Configuración
URL_OKRU = "https://ok.ru/live/10849691639514"  
ARCHIVO_M3U = "otro-repo/XOY"  
IDENTIFICADOR = 'tvg-name="CANAL13.mx"'  

def obtener_enlace_m3u8():
    try:
        print("Extrayendo URL dinámica de OK.ru...")
        resultado = subprocess.run(
            ["streamlink", URL_OKRU, "best", "--stream-url"],
            capture_output=True, text=True, check=True
        )
        url_extraida = resultado.stdout.strip()
        if "m3u8" in url_extraida:
            print("URL dinámica m3u8 obtenida con éxito.")
            return url_extraida
        print("Error: No se obtuvo un formato m3u8 válido.")
        return None
    except Exception as e:
        print(f"Error en la extracción con Streamlink: {e}")
        return None

def actualizar_linea_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo {ARCHIVO_M3U} no existe.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    nuevas_lineas = []
    modificado = False
    encontrado_canal = False

    print(f"Buscando el bloque de CANAL13.mx dentro de XOY...")

    for linea in lineas:
        # Si ya encontramos el #EXTINF del canal y vemos una línea que empieza con http, la cambiamos
        if encontrado_canal and (linea.strip().startswith("http://") or linea.strip().startswith("https://")):
            nuevas_lineas.append(nueva_url + "\n")
            encontrado_canal = False  # Terminamos el reemplazo para este canal
            modificado = True
            print("¡Línea de URL localizada y reemplazada con éxito!")
        else:
            nuevas_lineas.append(linea)
            # Detecta el inicio de tu canal
            if "#EXTINF" in linea and IDENTIFICADOR in linea:
                encontrado_canal = True

    if modificado:
        with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
            f.writelines(nuevas_lineas)
        print(f"¡Éxito total! Tu archivo XOY ha sido actualizado respetando las propiedades de Kodi.")
    else:
        print(f"⚠️ Error: No se pudo realizar el reemplazo. Verifica el formato de la URL vieja.")

if __name__ == "__main__":
    enlace = obtener_enlace_m3u8()
    if enlace:
        actualizar_linea_m3u(enlace)
