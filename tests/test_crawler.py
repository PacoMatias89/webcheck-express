import pytest
from unittest.mock import Mock

from webcheck.crawler import clasificar_respuesta, resolver_url, comprobar_enlace
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import Error as PlaywrightError


def test_comprobar_enlace_200():
    page = Mock()
    page.request.get.return_value.status = 200

    codigo, estado = comprobar_enlace(
        page,
        "http://127.0.0.1:8000/contacto.html"
    )

    assert codigo == 200
    assert estado == "CORRECTO"

    page.request.get.assert_called_once_with(
        "http://127.0.0.1:8000/contacto.html",
        timeout=5000,
        max_redirects=0
    )


def test_comprobar_enlace_404():
    page = Mock()

    page.request.get.return_value.status = 404

    codigo, estado = comprobar_enlace(
        page,
        "http://127.0.0.1:8000/servicios.html"
    )

    assert codigo == 404
    assert estado == "ENLACE ROTO"


def test_comprobar_enlace_timeout():
    page = Mock()

    page.request.get.side_effect = PlaywrightTimeoutError(
        "Timeout simulado"
    )

    codigo, estado = comprobar_enlace(
        page,
        "http://127.0.0.1:8000/servicios.html"
    )

    assert codigo is None
    assert estado == "TIMEOUT"


def test_comprobar_enlace_error_conexion():
    page = Mock()

    page.request.get.side_effect = PlaywrightError(
        "Error de conexión"
    )

    codigo, estado = comprobar_enlace(
        page,
        "http://127.0.0.1:8000/servicios.html"
    )

    assert codigo is None
    assert estado == "ERROR DE CONEXIÓN"


@pytest.mark.parametrize(
    "codigo, esperado",
    [
        (200, "CORRECTO"),
        (204, "CORRECTO"),
        (301, "REVISAR"),
        (404, "ENLACE ROTO"),
        (500, "REVISAR"),
    ]
)
def test_clasificar_respuesta(codigo, esperado):
    resultado = clasificar_respuesta(codigo)

    assert resultado == esperado


@pytest.mark.parametrize(
    "url, destino, esperado",
    [
        ("https://ejemplo.com/", "/contacto", "https://ejemplo.com/contacto"),
        ("https://ejemplo.com/blog/", "articulo",
         "https://ejemplo.com/blog/articulo"),
        ("https://ejemplo.com/", "https://otra.com/", "https://otra.com/"),
        ("https://ejemplo.com/", None, None),
        ("https://ejemplo.com/", "", None),
    ]
)
def test_resolver_url(url, destino, esperado):
    resultado = resolver_url(url, destino)
    assert resultado == esperado
