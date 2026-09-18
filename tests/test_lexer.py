import pytest
from prolog_lexer.lexer import analizar


@pytest.mark.parametrize(("texto", "tipo"), [
    ("padre", "ATOMO"),
    ("persona_1", "ATOMO"),
    ("'Juan Pérez'", "ATOMO"),
    ("':-'", "ATOMO"),
    ("X", "VARIABLE"),
    ("_Tmp", "VARIABLE"),
    ("_", "VARIABLE_ANONIMA"),
    ("25", "ENTERO"),
    ("3.14", "REAL"),
    ('"hola"', "CADENA"),
    (r'"a\n"', "CADENA"),
    (":-", "OP_REGLA"),
    ("?-", "OP_CONSULTA"),
    ("\\==", "OP_NO_IDENTIDAD"),
    ("=..", "OP_UNIV"),
    ("=<", "OP_MENOR_IGUAL"),
    ("**", "OP_POTENCIA"),
    ("//", "OP_DIVISION_ENTERA"),
    ("is", "OP_IS"),
    ("mod", "OP_MOD"),
    ("\\+", "OP_NEGACION"),
    ("!", "CORTE"),
    (";", "PUNTO_COMA"),
    ("|", "BARRA_VERTICAL"),
])
def test_token_individual(texto, tipo):
    resultado = analizar(texto)

    assert not resultado.errores
    assert len(resultado.tokens) == 1

    token = resultado.tokens[0]

    assert (
        token.tipo,
        token.lexema,
        token.linea,
        token.columna,
    ) == (tipo, texto, 1, 1)


@pytest.mark.parametrize(("texto", "codigo"), [
    ("@", "CARACTER_NO_ADMITIDO"),
    (":", "CARACTER_NO_ADMITIDO"),
    ("'abierto", "ATOMO_SIN_CIERRE"),
    ('"abierta', "CADENA_SIN_CIERRE"),
    ("/* abierto", "COMENTARIO_SIN_CIERRE"),
    ("12abc", "NUMERO_MAL_FORMADO"),
    ("1e3", "NUMERO_MAL_FORMADO"),
    ("1_000", "NUMERO_MAL_FORMADO"),
    (r'"a\q"', "ESCAPE_INVALIDO"),
    ('"a\tb"', "CONTROL_EN_LITERAL"),
])
def test_error(texto, codigo):
    resultado = analizar(texto)

    assert not resultado.tokens
    assert not resultado.lexemas
    assert len(resultado.errores) == 1

    assert resultado.errores[0].codigo == codigo
    assert resultado.errores[0].fragmento == texto


def test_limites_y_prioridades():
    resultado = analizar("is isla 'is' _ _Tmp -25 3.14. \\== =.. **")

    assert not resultado.errores

    assert [t.tipo for t in resultado.tokens] == [
        "OP_IS",
        "ATOMO",
        "ATOMO",
        "VARIABLE_ANONIMA",
        "VARIABLE",
        "OP_MENOS",
        "ENTERO",
        "REAL",
        "PUNTO",
        "OP_NO_IDENTIDAD",
        "OP_UNIV",
        "OP_POTENCIA",
    ]


@pytest.mark.parametrize("salto", ["\n", "\r\n", "\r"])
def test_posiciones_y_comentarios(salto):
    resultado = analizar(f"% inicio{salto}/* a{salto}b */\tX.")

    assert not resultado.errores

    assert [
        (t.lexema, t.linea, t.columna)
        for t in resultado.tokens
    ] == [
        ("X", 3, 6),
        (".", 3, 7),
    ]


def test_tabla_de_lexemas():
    resultado = analizar("padre(X). padre(X). 'padre'.")

    assert not resultado.errores

    assert [
        (e.indice, e.tipo, e.lexema)
        for e in resultado.lexemas
    ] == [
        (0, "ATOMO", "padre"),
        (1, "VARIABLE", "X"),
        (2, "ATOMO", "'padre'"),
    ]

    assert [
        t.indice_lexema
        for t in resultado.tokens
        if t.tipo == "ATOMO"
    ] == [0, 0, 2]

    assert all(
        t.indice_lexema is None
        for t in resultado.tokens
        if t.tipo == "PUNTO"
    )


def test_recuperacion():
    resultado = analizar('@ X\n12abc, Y\n"abierta\nZ.')

    assert [
        (t.lexema, t.linea, t.columna)
        for t in resultado.tokens
    ] == [
        ("X", 1, 3),
        (",", 2, 6),
        ("Y", 2, 8),
        ("Z", 4, 1),
        (".", 4, 2),
    ]

    assert [
        (e.codigo, e.linea, e.columna)
        for e in resultado.errores
    ] == [
        ("CARACTER_NO_ADMITIDO", 1, 1),
        ("NUMERO_MAL_FORMADO", 2, 1),
        ("CADENA_SIN_CIERRE", 3, 1),
    ]


def test_marcadores_dentro_de_comillas():
    resultado = analizar('"% /* texto */"')

    assert not resultado.errores
    assert len(resultado.tokens) == 1
    assert resultado.tokens[0].tipo == "CADENA"


def test_entrada_vacia():
    resultado = analizar("")

    assert resultado.tokens == resultado.lexemas == resultado.errores == []
