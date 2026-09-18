from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    tipo: str
    lexema: str
    linea: int
    columna: int
    indice_lexema: int | None = None


@dataclass(frozen=True)
class ErrorLexico:
    codigo: str
    mensaje: str
    fragmento: str
    linea: int
    columna: int


@dataclass(frozen=True)
class EntradaLexema:
    indice: int
    tipo: str
    lexema: str


@dataclass
class Resultado:
    tokens: list[Token]
    lexemas: list[EntradaLexema]
    errores: list[ErrorLexico]
