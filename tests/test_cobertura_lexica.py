import pytest

from prolog_lexer.lexer import analizar


@pytest.mark.parametrize(("texto", "tipo"), [
    ("=", "OP_UNIFICACION"),
    ("\\=", "OP_NO_UNIFICACION"),
    ("==", "OP_IDENTIDAD"),
    ("<", "OP_MENOR"),
    (">", "OP_MAYOR"),
    (">=", "OP_MAYOR_IGUAL"),
    ("+", "OP_MAS"),
    ("-", "OP_MENOS"),
    ("*", "OP_MULTIPLICACION"),
    ("/", "OP_DIVISION"),
    (",", "COMA"),
    ("(", "PARENTESIS_IZQ"),
    (")", "PARENTESIS_DER"),
    ("[", "CORCHETE_IZQ"),
    ("]", "CORCHETE_DER"),
    ("{", "LLAVE_IZQ"),
    ("}", "LLAVE_DER"),
    (".", "PUNTO"),
])
def test_simbolos_pendientes(texto, tipo):
    resultado = analizar(texto)

    assert not resultado.errores
    assert not resultado.lexemas
    assert len(resultado.tokens) == 1

    token = resultado.tokens[0]

    assert (
        token.tipo,
        token.lexema,
        token.linea,
        token.columna,
    ) == (tipo, texto, 1, 1)

    assert token.indice_lexema is None


@pytest.mark.parametrize(
    ("comilla", "tipo"),
    [("'", "ATOMO"), ('"', "CADENA")],
)
@pytest.mark.parametrize(
    "escape",
    [r"\\", r"\'", r'\"', r"\n", r"\r", r"\t"],
)
def test_escapes_admitidos(comilla, tipo, escape):
    literal = comilla + escape + comilla
    resultado = analizar(literal + " X")

    assert not resultado.errores

    assert [
        (t.tipo, t.lexema)
        for t in resultado.tokens
    ] == [
        (tipo, literal),
        ("VARIABLE", "X"),
    ]

    assert (
        resultado.tokens[1].linea,
        resultado.tokens[1].columna,
    ) == (1, 6)


@pytest.mark.parametrize(("texto", "esperados"), [
    (
        "25.",
        [("ENTERO", "25"), ("PUNTO", ".")],
    ),
    (
        ".5",
        [("PUNTO", "."), ("ENTERO", "5")],
    ),
    (
        "1.2.3",
        [("REAL", "1.2"), ("PUNTO", "."), ("ENTERO", "3")],
    ),
    (
        "'a''b'",
        [("ATOMO", "'a'"), ("ATOMO", "'b'")],
    ),
    (
        "'' \"\"",
        [("ATOMO", "''"), ("CADENA", '""')],
    ),
    (
        "island mod2 __",
        [("ATOMO", "island"), ("ATOMO", "mod2"), ("VARIABLE", "__")],
    ),
])
def test_limites_de_lexemas(texto, esperados):
    resultado = analizar(texto)

    assert not resultado.errores

    assert [
        (t.tipo, t.lexema)
        for t in resultado.tokens
    ] == esperados


@pytest.mark.parametrize("texto", [
    "% sin salto final",
    "/**/",
    "/* bloque */",
    " \t\r\n",
])
def test_entrada_sin_tokens(texto):
    resultado = analizar(texto)

    assert resultado.tokens == resultado.lexemas == resultado.errores == []


def test_comentario_de_bloque_no_anidado():
    resultado = analizar("/* uno /* dos */X")

    assert not resultado.errores

    assert [
        (t.tipo, t.lexema, t.linea, t.columna)
        for t in resultado.tokens
    ] == [
        ("VARIABLE", "X", 1, 17),
    ]


@pytest.mark.parametrize(
    ("texto", "codigo", "pos_error", "pos_x"),
    [
        (
            r'"a\q" X',
            "ESCAPE_INVALIDO",
            (1, 3),
            (1, 7),
        ),
        (
            r"'a\q' X",
            "ESCAPE_INVALIDO",
            (1, 3),
            (1, 7),
        ),
        (
            '"a\tb" X',
            "CONTROL_EN_LITERAL",
            (1, 3),
            (1, 7),
        ),
        (
            "'sin cierre\r\nX",
            "ATOMO_SIN_CIERRE",
            (1, 1),
            (2, 1),
        ),
        (
            '"sin cierre\nX',
            "CADENA_SIN_CIERRE",
            (1, 1),
            (2, 1),
        ),
        (
            "2.5kg X",
            "NUMERO_MAL_FORMADO",
            (1, 1),
            (1, 7),
        ),
        (
            "0xFF X",
            "NUMERO_MAL_FORMADO",
            (1, 1),
            (1, 6),
        ),
    ],
)
def test_posiciones_y_recuperacion(texto, codigo, pos_error, pos_x):
    resultado = analizar(texto)

    assert len(resultado.errores) == 1

    error = resultado.errores[0]

    assert error.codigo == codigo
    assert (error.linea, error.columna) == pos_error

    assert [
        (t.tipo, t.lexema)
        for t in resultado.tokens
    ] == [
        ("VARIABLE", "X"),
    ]

    assert (
        resultado.tokens[0].linea,
        resultado.tokens[0].columna,
    ) == pos_x

    assert [
        (e.tipo, e.lexema)
        for e in resultado.lexemas
    ] == [
        ("VARIABLE", "X"),
    ]


@pytest.mark.parametrize(("texto", "codigo"), [
    ('"texto\\', "CADENA_SIN_CIERRE"),
    ("'a\\'", "ATOMO_SIN_CIERRE"),
])
def test_escape_al_final_sin_cierre(texto, codigo):
    resultado = analizar(texto)

    assert not resultado.tokens
    assert not resultado.lexemas
    assert len(resultado.errores) == 1

    assert resultado.errores[0].codigo == codigo
    assert resultado.errores[0].fragmento == texto
