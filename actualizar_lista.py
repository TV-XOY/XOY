import os
import re

ARCHIVO_M3U = "XOY"

# CONFIGURACIÓN: Reemplaza con tus datos exactos de GitHub Pages obtenidos en el paso 1
USUARIO_GITHUB = "TV-XOY"       # <-- Pon tu nombre de usuario de GitHub aquí
REPOSITORIO_GITHUB = "XOY" # <-- Pon el nombre de tu repositorio aquí

def generar_lista_estatica():
    if not os.path.exists(ARCHIVO_M3U):
        print(f"Error: El archivo '{ARCHIVO_M3U}' no se encuentra en la raíz.")
        return

    with open(ARCHIVO_M3U, "r", encoding="utf-8") as f:
        contenido = f.read()

    # URL definitiva que procesará la redirección en tiempo real usando la IP del reproductor
    url_redireccion_permanente = f"https://{USUARIO_GITHUB}.github.io/{REPOSITORIO_GITHUB}/canal13merida.m3u8"

    # Estructura limpia M3U sin duplicados de User-Agent ni parámetros incompatibles
    parametros_fijos = (
        '#EXTINF:-1 tvg-name="CANAL13.mx" tvg-chno="13" tvg-id="CANAL13.mx" '
        'tvg-logo="https://canal13mexico.com" '
        'group-title="NACIONALES",CANAL 13 MERIDA\n'
        '#EXTVLCOPT:network-caching=2000\n'
        '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Mobile Safari/537.36\n'
        '#EXTVLCOPT--http-reconnect=true'
    )

    # Expresión regular mejorada para detectar cualquier variante previa del Canal 13 Mérida y evitar duplicados
    patron = r'(#EXTINF:-1.*?CANAL 13 MERIDA\n.*?)(https?://[^\s]+)'
    
    if re.search(patron, contenido):
        # Reemplaza de forma limpia el bloque antiguo eliminando las cabeceras extras del intento anterior
        nuevo_contenido = re.sub(patron, f"{parametros_fijos}\n{url_redireccion_permanente}", contenido)
        print("Estructura localizada. Canal 13 Mérida actualizado con éxito y sin duplicados.")
    else:
        print("Bloque previo no detectado en XOY. Añadiendo canal de forma limpia al final.")
        nuevo_contenido = contenido.rstrip() + f"\n\n{parametros_fijos}\n{url_redireccion_permanente}\n"

    with open(ARCHIVO_M3U, "w", encoding="utf-8") as f:
        f.write(nuevo_contenido)
    
    # Creamos el archivo de enlace de reproducción automática (Play-List indexada)
    # Esto le dice al reproductor que cargue el script de procesamiento dinámico directo
    with open("canal13merida.m3u8", "w", encoding="utf-8") as f:
        f.write(f"#EXTM3U\n{parametros_fijos}\nhttps://ok.ru")
    print("Archivo de redirección indexado correctamente.")

if __name__ == "__main__":
    generar_lista_estatica()
