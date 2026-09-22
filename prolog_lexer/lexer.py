from collections.abc import Callable

from .modelos import EntradaLexema, ErrorLexico, Resultado, Token
from .visualizador import generar_grafo_completo

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
    def __init__(self, texto: str, nombre_unico: str = "default", exportar_grafos: bool = False):
        self.texto = texto
        self.nombre_unico = nombre_unico
        self.pos = 0
        self.linea = 1
        self.columna = 1
        self.resultado = Resultado([], [], [])
        self.indices: dict[tuple[str, str], int] = {}

        # --- CONTROL DE GRAFOS INDIVIDUALES ---
        self.exportar_grafos = exportar_grafos
        self.contador_tokens = 1  # Índice n para el nombre de la imagen
        self.estado_actual = "q0"
        self.contador_estados = 0
        self.historial_transiciones: list[tuple[str, str, str]] = []

    def nuevo_estado(self, prefijo: str = "q") -> str:
        self.contador_estados += 1
        return f"{prefijo}{self.contador_estados}"

    def reset_transiciones(self) -> None:
        self.estado_actual = "q0"
        self.contador_estados = 0
        self.historial_transiciones = []

    def actual(self, desplazamiento: int = 0) -> str:
        pos = self.pos + desplazamiento
        return self.texto[pos] if pos < len(self.texto) else ""

    def avanzar(self) -> None:
        c = self.actual()

        if not c: return

        # Registrar transición local para el token actual
        siguiente_estado = self.nuevo_estado()
        simbolo_etiqueta = repr(c)[1:-1] if c in "\r\n\t" else c
        
        self.historial_transiciones.append(
            (self.estado_actual, simbolo_etiqueta, siguiente_estado)
        )
        self.estado_actual = siguiente_estado

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

        # GENERAR EL GRAFO ÚNICAMENTE SI SE EMITE UN TOKEN REGISTRADO
        if self.exportar_grafos and self.historial_transiciones and indice is not None:
            # Usamos el índice único del lexema asignado por registrar_lexema
            nombre_archivo = f"grafo_{indice}"
            generar_grafo_completo(
                self.historial_transiciones, 
                lexema, 
                tipo, 
                nombre_archivo,
                self.nombre_unico
            )

        # REINICIAR inmediatamente el estado para el siguiente lexema
        self.reset_transiciones()

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
        self.reset_transiciones()

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

        self.reset_transiciones()

        if c in ESPACIO_EN_BLANCO:
            self.avanzar()
            self.reset_transiciones()

        elif c == "%":
            self.comentario_linea()
            self.reset_transiciones()

        elif self.coincide("/*"):
            self.comentario_bloque(inicio, linea, columna)
            self.reset_transiciones()

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


def analizar(texto: str, exportar_grafos: bool = False) -> Resultado:
    return Lexer(texto, exportar_grafos=exportar_grafos).analizar()
