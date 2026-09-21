from collections.abc import Callable

from .modelos import EntradaLexema, ErrorLexico, Resultado, Token

SIMBOLOS = {
    ":-": "OP_REGLA", "?-": "OP_CONSULTA",
    "=": "OP_UNIFICACION", "\\=": "OP_NO_UNIFICACION",
    "==": "OP_IDENTIDAD", "\\==": "OP_NO_IDENTIDAD",
    "=..": "OP_UNIV", "<": "OP_MENOR", "=<": "OP_MENOR_IGUAL",
    ">": "OP_MAYOR", ">=": "OP_MAYOR_IGUAL",
    "+": "OP_MAS", "-": "OP_MENOS", "*": "OP_MULTIPLICACION",
    "/": "OP_DIVISION", "//": "OP_DIVISION_ENTERA", "**": "OP_POTENCIA",
    "\\+": "OP_NEGACION", "!": "CORTE", ";": "PUNTO_COMA", ",": "COMA",
    "(": "PARENTESIS_IZQ", ")": "PARENTESIS_DER",
    "[": "CORCHETE_IZQ", "]": "CORCHETE_DER",
    "{": "LLAVE_IZQ", "}": "LLAVE_DER", "|": "BARRA_VERTICAL", ".": "PUNTO",
}
SIMBOLOS_ORDENADOS = sorted(SIMBOLOS, key=len, reverse=True)
PALABRAS_OPERADORAS = {"is": "OP_IS", "mod": "OP_MOD"}
REGISTRABLES = {"ATOMO", "VARIABLE", "VARIABLE_ANONIMA", "ENTERO", "REAL", "CADENA"}
ESCAPES = {"\\", "'", '"', "n", "r", "t"}
ESPACIO_EN_BLANCO = " \t\r\n"
FIN_DE_LINEA = "\r\n"

Posicion = tuple[int, int, int]


def es_letra(c: str) -> bool:
    return "a" <= c <= "z" or "A" <= c <= "Z"


def es_digito(c: str) -> bool:
    return "0" <= c <= "9"


def es_continuacion(c: str) -> bool:
    return es_letra(c) or es_digito(c) or c == "_"


class Lexer:
    def __init__(self, texto: str):
        self.texto = texto
        self.pos = 0
        self.linea = 1
        self.columna = 1
        self.resultado = Resultado([], [], [])
        self.indices: dict[tuple[str, str], int] = {}

    def actual(self, desplazamiento: int = 0) -> str:
        pos = self.pos + desplazamiento
        return self.texto[pos] if pos < len(self.texto) else ""

    def avanzar(self) -> None:
        c = self.actual()

        if not c:
            return

        self.pos += 1

        if c == "\r":
            if self.actual() == "\n":
                self.pos += 1

            self.linea += 1
            self.columna = 1

        elif c == "\n":
            self.linea += 1
            self.columna = 1

        else:
            self.columna += 1

    def coincide(self, texto: str) -> bool:
        return self.texto.startswith(texto, self.pos)

    def origen(self) -> Posicion:
        """Devuelve el índice y coordenadas del carácter actual."""
        return self.pos, self.linea, self.columna

    def avanzar_mientras(self, condicion: Callable[[str], bool]) -> None:
        while condicion(self.actual()):
            self.avanzar()

    def registrar_lexema(self, tipo: str, lexema: str) -> int | None:
        if tipo not in REGISTRABLES:
            return None

        clave = (tipo, lexema)
        indice = self.indices.get(clave)

        if indice is None:
            indice = len(self.resultado.lexemas)
            self.indices[clave] = indice
            self.resultado.lexemas.append(EntradaLexema(indice, tipo, lexema))

        return indice

    def emitir(
        self,
        tipo: str,
        inicio: int,
        linea: int,
        columna: int,
    ) -> None:
        lexema = self.texto[inicio:self.pos]
        indice = self.registrar_lexema(tipo, lexema)

        self.resultado.tokens.append(
            Token(tipo, lexema, linea, columna, indice)
        )

    def error(
        self,
        codigo: str,
        mensaje: str,
        inicio: int,
        linea: int,
        columna: int,
    ) -> None:
        self.resultado.errores.append(
            ErrorLexico(
                codigo,
                mensaje,
                self.texto[inicio:self.pos],
                linea,
                columna,
            )
        )

    def identificador(
        self,
        inicio: int,
        linea: int,
        columna: int,
    ) -> None:
        self.avanzar_mientras(es_continuacion)

        lexema = self.texto[inicio:self.pos]

        if lexema == "_":
            tipo = "VARIABLE_ANONIMA"

        elif lexema[0] == "_" or "A" <= lexema[0] <= "Z":
            tipo = "VARIABLE"

        else:
            tipo = PALABRAS_OPERADORAS.get(lexema, "ATOMO")

        self.emitir(tipo, inicio, linea, columna)

    def numero(
        self,
        inicio: int,
        linea: int,
        columna: int,
    ) -> None:
        self.avanzar_mientras(es_digito)

        tipo = "ENTERO"

        if self.actual() == "." and es_digito(self.actual(1)):
            tipo = "REAL"
            self.avanzar()

            self.avanzar_mientras(es_digito)

        if es_letra(self.actual()) or self.actual() == "_":
            self.avanzar_mientras(es_continuacion)

            self.error(
                "NUMERO_MAL_FORMADO",
                "Sufijo numérico no admitido",
                inicio,
                linea,
                columna,
            )
            return

        self.emitir(tipo, inicio, linea, columna)

    def entre_comillas(
        self,
        inicio: int,
        linea: int,
        columna: int,
    ) -> None:
        comilla = self.actual()
        tipo = "ATOMO" if comilla == "'" else "CADENA"
        problema = None

        self.avanzar()

        while self.actual() and self.actual() not in FIN_DE_LINEA:
            c = self.actual()

            if c == comilla:
                self.avanzar()

                if problema is None:
                    self.emitir(tipo, inicio, linea, columna)
                else:
                    codigo, mensaje, lin, col = problema
                    self.error(codigo, mensaje, inicio, lin, col)

                return

            if c == "\\":
                if self.actual(1) not in ESCAPES and problema is None:
                    problema = (
                        "ESCAPE_INVALIDO",
                        "Escape no admitido",
                        self.linea,
                        self.columna,
                    )

                self.avanzar()

                if self.actual() and self.actual() not in "\r\n":
                    self.avanzar()

                continue

            if (ord(c) < 32 or ord(c) == 127) and problema is None:
                problema = (
                    "CONTROL_EN_LITERAL",
                    "Control sin escapar",
                    self.linea,
                    self.columna,
                )

            self.avanzar()

        self.error(
            f"{tipo}_SIN_CIERRE",
            "Falta la comilla de cierre",
            inicio,
            linea,
            columna,
        )

    def comentario_bloque(
        self,
        inicio: int,
        linea: int,
        columna: int,
    ) -> None:
        self.avanzar()
        self.avanzar()

        while self.actual() and not self.coincide("*/"):
            self.avanzar()

        if not self.actual():
            self.error(
                "COMENTARIO_SIN_CIERRE",
                "Falta */",
                inicio,
                linea,
                columna,
            )
            return

        self.avanzar()
        self.avanzar()

    def comentario_linea(self) -> None:
        self.avanzar_mientras(lambda caracter: caracter not in FIN_DE_LINEA)

    def simbolo(self, inicio: int, linea: int, columna: int) -> bool:
        for texto in SIMBOLOS_ORDENADOS:
            if self.coincide(texto):
                for _ in texto:
                    self.avanzar()

                self.emitir(SIMBOLOS[texto], inicio, linea, columna)
                return True

        return False

    def analizar_unidad(self) -> None:
        inicio, linea, columna = self.origen()
        c = self.actual()

        if c in ESPACIO_EN_BLANCO:
            self.avanzar()

        elif c == "%":
            self.comentario_linea()

        elif self.coincide("/*"):
            self.comentario_bloque(inicio, linea, columna)

        elif c in "'\"":
            self.entre_comillas(inicio, linea, columna)

        elif es_letra(c) or c == "_":
            self.identificador(inicio, linea, columna)

        elif es_digito(c):
            self.numero(inicio, linea, columna)

        elif not self.simbolo(inicio, linea, columna):
            self.avanzar()
            self.error(
                "CARACTER_NO_ADMITIDO",
                "Carácter no admitido",
                inicio,
                linea,
                columna,
            )

    def analizar(self) -> Resultado:
        while self.actual():
            self.analizar_unidad()

        return self.resultado


def analizar(texto: str) -> Resultado:
    return Lexer(texto).analizar()
