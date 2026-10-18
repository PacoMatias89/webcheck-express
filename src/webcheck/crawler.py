
import argparse

from urllib.parse import urljoin, urlsplit

from playwright.sync_api import (
    sync_playwright,
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
)


# --------------------------------------------------
# 1. Clasificación de respuestas HTTP
# --------------------------------------------------
def clasificar_respuesta(codigo_http: int) -> str:
    if codigo_http == 404:
        return "ENLACE ROTO"

    if 200 <= codigo_http < 300:
        return "CORRECTO"

    return "REVISAR"


# --------------------------------------------------
# 2. Resolución de URLs
# --------------------------------------------------
def resolver_url(url_base: str, destino: str | None) -> str | None:
    if not destino:
        return None

    url_completa = urljoin(url_base, destino)

    return url_completa


# --------------------------------------------------
# 3. Comprobación HTTP de enlaces
# --------------------------------------------------
def comprobar_enlace(page, url: str) -> tuple[int | None, str]:
    try:
        respuesta = page.request.get(
            url,
            timeout=5000,
            max_redirects=0
        )

        codigo = respuesta.status
        estado = clasificar_respuesta(codigo)

        return codigo, estado

    except PlaywrightTimeoutError:
        return None, "TIMEOUT"

    except PlaywrightError:
        return None, "ERROR DE CONEXIÓN"


# --------------------------------------------------
# 4. Análisis de la página
# --------------------------------------------------
def analizar_pagina(url: str) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)

        try:
            try:
                page = browser.new_page()

                response = page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=15000
                )

            except PlaywrightTimeoutError as error:
                print(f"TIMEOUT al abrir la página: {error}")
                return

            except PlaywrightError as error:
                print(f"ERROR al abrir la página: {error}")
                return

            # Información general de la página
            titulo = page.title()
            print(f"Título: {titulo}")

            enlaces = page.locator("a[href]")
            numero_enlaces = enlaces.count()
            print(f"Enlaces encontrados: {numero_enlaces}")

            # Recorremos los enlaces encontrados
            for i in range(numero_enlaces):
                enlace_actual = enlaces.nth(i)
                destino = enlace_actual.get_attribute("href")

                # Resolvemos la URL
                url_completa = resolver_url(page.url, destino)

                # Si no existe destino, pasamos al siguiente enlace
                if url_completa is None:
                    print(f"Enlace {i + 1}: SIN DESTINO")
                    continue

                datos_url = urlsplit(url_completa)
                print(f"Enlace {i + 1}: {url_completa}")

                # Por ahora comprobamos solo nuestro servidor local
                if (
                    datos_url.scheme == "http"
                    and datos_url.hostname == "127.0.0.1"
                    and datos_url.port == 8000
                ):
                    codigo_enlace, estado_enlace = comprobar_enlace(
                        page,
                        url_completa
                    )

                    print(f"Estado HTTP del enlace: {codigo_enlace}")
                    print(f"Resultado: {estado_enlace}\n")

            # Información final de la página analizada
            url_final = page.url
            codigo_http = response.status if response else None

            print(f"URL final: {url_final}")
            print(f"Código HTTP: {codigo_http}")

        finally:
            browser.close()


# --------------------------------------------------
# 5. Punto de entrada
# --------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Primera navegación de WebCheck Express"
    )

    parser.add_argument(
        "url",
        help="URL que queremos analizar"
    )

    argumentos = parser.parse_args()

    analizar_pagina(argumentos.url)
