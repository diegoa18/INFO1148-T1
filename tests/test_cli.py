from pathlib import Path
import subprocess
import sys


RAIZ = Path(__file__).resolve().parents[1]


def ejecutar(ruta: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "prolog_lexer", str(ruta)],
        cwd=RAIZ,
        capture_output=True,
        encoding="utf-8",
        timeout=10,
        check=False,
    )


def test_archivo_completo_valido():
    proceso = ejecutar(RAIZ / "ejemplos" / "valido.pl")

    assert proceso.returncode == 0
    assert proceso.stderr == ""

    assert "<ATOMO, 'padre', 2, 1>" in proceso.stdout
    assert "<VARIABLE, 'Resto', 14, 15>" in proceso.stdout
    assert "TABLA DE LEXEMAS" in proceso.stdout


def test_archivo_completo_con_errores():
    proceso = ejecutar(RAIZ / "ejemplos" / "con_errores.pl")

    assert proceso.returncode == 1
    assert "<VARIABLE, 'Quien', 7, 16>" in proceso.stdout

    lineas = proceso.stderr.strip().splitlines()

    assert lineas[0] == "ERRORES"
    assert len(lineas) == 5

    for prefijo, linea in zip([
        "2:1 CARACTER_NO_ADMITIDO:",
        "3:7 NUMERO_MAL_FORMADO:",
        "4:9 CADENA_SIN_CIERRE:",
        "6:9 ATOMO_SIN_CIERRE:",
    ], lineas[1:]):
        assert linea.startswith(prefijo)


def test_archivo_inexistente(tmp_path):
    proceso = ejecutar(tmp_path / "no_existe.pl")

    assert proceso.returncode == 2
    assert proceso.stdout == ""
    assert proceso.stderr.startswith("Error de entrada:")


def test_archivo_con_utf8_invalido(tmp_path):
    ruta = tmp_path / "codificacion_invalida.pl"
    ruta.write_bytes(b"\xff")

    proceso = ejecutar(ruta)

    assert proceso.returncode == 2
    assert proceso.stdout == ""
    assert proceso.stderr.startswith("Error de entrada:")
