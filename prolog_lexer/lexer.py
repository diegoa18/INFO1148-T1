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

    def emitir(
        self,
        tipo: str,
        inicio: int,
        linea: int,
        columna: int,
    ) -> None:
        lexema = self.texto[inicio:self.pos]
        indice = None

        if tipo in REGISTRABLES:
            clave = (tipo, lexema)

            if clave not in self.indices:
                self.indices[clave] = len(self.resultado.lexemas)
                self.resultado.lexemas.append(
                    EntradaLexema(self.indices[clave], tipo, lexema)
                )

            indice = self.indices[clave]

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
        while es_continuacion(self.actual()):
            self.avanzar()

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
        while es_digito(self.actual()):
            self.avanzar()

        tipo = "ENTERO"

        if self.actual() == "." and es_digito(self.actual(1)):
            tipo = "REAL"
            self.avanzar()

            while es_digito(self.actual()):
                self.avanzar()

        if es_letra(self.actual()) or self.actual() == "_":
            while es_continuacion(self.actual()):
                self.avanzar()

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

        while self.actual() and self.actual() not in "\r\n":
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

    def analizar(self) -> Resultado:
        while self.actual():
            inicio = self.pos
            linea = self.linea
            columna = self.columna
            c = self.actual()

            if c in " \t\r\n":
                self.avanzar()

            elif c == "%":
                while self.actual() and self.actual() not in "\r\n":
                    self.avanzar()

            elif self.coincide("/*"):
                self.comentario_bloque(inicio, linea, columna)

            elif c in "'\"":
                self.entre_comillas(inicio, linea, columna)

            elif es_letra(c) or c == "_":
                self.identificador(inicio, linea, columna)

            elif es_digito(c):
                self.numero(inicio, linea, columna)

            else:
                for simbolo in SIMBOLOS_ORDENADOS:
                    if self.coincide(simbolo):
                        for _ in simbolo:
                            self.avanzar()

                        self.emitir(
                            SIMBOLOS[simbolo],
                            inicio,
                            linea,
                            columna,
                        )
                        break
                else:
                    self.avanzar()
                    self.error(
                        "CARACTER_NO_ADMITIDO",
                        "Carácter no admitido",
                        inicio,
                        linea,
                        columna,
                    )

        return self.resultado


def analizar(texto: str) -> Resultado:
    return Lexer(texto).analizar()
