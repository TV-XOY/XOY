import os
import subprocess

# CONFIGURACIÓN GENERAL
URL_OKRU = "https://ok.ru"
ARCHIVO_M3U = "otro-repo/XOY"  # Ruta donde la Action descargará tu lista XOY
IDENTIFICADOR = 'tvg-name="CANAL13.mx"'  # Parámetro clave en tu lista

def obtener_enlace_m3u8():
    try:
        print("Iniciando extracción con Streamlink...")
        # Simula el reproductor y extrae la URL cruda del directo de OK.ru
        resultado = subprocess.run(
            ["streamlink", URL_OKRU, "best", "--stream-url"],
            capture_output=True, text=True, check=True
        )
        url_extraida = resultado.stdout.strip()
        if "m3u8" in url_extraida:
            print("¡Enlace dinámico extraído exitosamente!")
            return url_extraida
        print("Error: El resultado no contiene un formato m3u8 válido.")
        return None
    except Exception as e:
        print(f"Error crítico en la extracción con Streamlink: {e}")
        return None

def actualizar_linea_m3u(nueva_url):
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error crítico: El archivo '{ARCHIVO_M3U}' no existe. Revisa la Action.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    nuevas_lineas = []
    modificado = False
    encontrado_canal = False

    print(f"Escaneando el archivo XOY para localizar {IDENTIFICADOR}...")

    for linea in lineas:
        # Si ya detectamos el canal y encontramos la línea de la URL vieja
        if encontrado_canal and (linea.strip().startswith("http://") or linea.strip().startswith("https://")):
            nuevas_lineas.append(nueva_url + "\n")
            encontrado_canal = False  # Apagamos la bandera tras actualizar
            modificado = True
            print("-> ¡URL localizada y reemplazada correctamente!")
        else:
            nuevas_lineas.append(linea)
            # Detecta la cabecera exacta de tu canal 13
            if "#EXTINF" in linea and IDENTIFICADOR in linea:
                encontrado_canal = True

    if modificado:
        with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
            f.writelines(nuevas_lineas)
        print("¡Proceso exitoso! Tu archivo XOY ha sido modificado localmente.")
    else:
        print(f"⚠️ Error: No se pudo realizar el cambio. Revisa que exista '{IDENTIFICADOR}' en XOY.")

if __name__ == "__main__":
    enlace = obtener_enlace_m3u8()
    if enlace:
        actualizar_linea_m3u(enlace)
