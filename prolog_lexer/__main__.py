import argparse
import sys
from .lexer import Lexer

def main() -> int:
    parser = argparse.ArgumentParser(description="Analizador léxico de Prolog para INFO1148")
    parser.add_argument("archivo", help="Archivo fuente UTF-8")
    parser.add_argument(
        "--grafo",
        nargs="?",
        const="flujo_automata",
        default=None,
        help="Genera un diagrama PNG del flujo del autómata (opcional: especifica el nombre del archivo)",
    )
    args = parser.parse_args()

    try:
        with open(args.archivo, encoding="utf-8", newline="") as archivo:
            texto = archivo.read()
    except (OSError, UnicodeError) as error:
        print(f"Error de entrada: {error}", file=sys.stderr)
        return 2

    nombre_test = args.archivo.rsplit(".", 1)[0]
    nombre_unico = nombre_test.rsplit("/", 1)[-1]

    exportar = args.grafo is not None

    lexer = Lexer(texto, nombre_unico, exportar_grafos=exportar)
    resultado = lexer.analizar()

    print("TOKENS")
    for token in resultado.tokens:
        print(
            f"<{token.tipo}, {token.lexema!r}, "
            f"{token.linea}, {token.columna}>"
        )

    print("\nTABLA DE LEXEMAS")
    for entrada in resultado.lexemas:
        print(f"{entrada.indice}: {entrada.tipo} {entrada.lexema!r}")

    if resultado.errores:
        print("\nERRORES", file=sys.stderr)

        for error in resultado.errores:
            print(
                f"{error.linea}:{error.columna} {error.codigo}: "
                f"{error.mensaje}; fragmento={error.fragmento!r}",
                file=sys.stderr,
            )

    return 1 if resultado.errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
