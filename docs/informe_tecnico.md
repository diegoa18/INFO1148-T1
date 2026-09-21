# Informe técnico: analizador léxico de un subconjunto de Prolog

> Documento fuente para el informe final. Completar con portada, integrantes, fecha, diagramas visuales y referencias antes de exportarlo a PDF.

## 1. Objetivo y alcance

Se implementó un analizador léxico para un subconjunto de Prolog. Recorre el texto de izquierda a derecha y produce tokens con tipo, lexema, línea y columna. También mantiene una tabla de lexemas y reporta errores recuperables. El alcance termina en el análisis léxico: no se valida la gramática, aridad, ámbitos ni unificación.

## 2. Especificación léxica

Convenciones: `L = [a-zA-Z]`, `D = [0-9]` y `C = [a-zA-Z0-9_]`.

| Categoría | Token | Patrón / forma admitida | Ejemplos |
|---|---|---|---|
| Átomo simple | `ATOMO` | `[a-z][a-zA-Z0-9_]*` | `padre`, `persona_1` |
| Átomo citado | `ATOMO` | Comillas simples; admite escapes definidos | `'Juan Pérez'`, `':-'` |
| Variable | `VARIABLE` | `[A-Z_][a-zA-Z0-9_]*`, excepto `_` | `X`, `_Temporal` |
| Variable anónima | `VARIABLE_ANONIMA` | `_` | `_` |
| Entero | `ENTERO` | `[0-9]+` | `25`, `0` |
| Real | `REAL` | `[0-9]+\.[0-9]+` | `3.14` |
| Cadena | `CADENA` | Comillas dobles; admite escapes definidos | `"hola"`, `"a\\n"` |
| Palabra operadora | `OP_IS`, `OP_MOD` | `is` o `mod`, completos | `X is 2`, `X mod 2` |

Se reconocen además `:-`, `?-`, `=`, `\\=`, `==`, `\\==`, `=..`, `<`, `=<`, `>`, `>=`, `+`, `-`, `*`, `/`, `//`, `**`, `\\+`, `!`, `;`, `,`, `(`, `)`, `[`, `]`, `{`, `}`, `|` y `.`. Los comentarios (`%` y `/* ... */`) y el espacio en blanco se ignoran, preservando línea y columna.

## 3. Prioridad y máxima coincidencia

Los símbolos se ordenan por longitud descendente. Así `\\==` se reconoce antes que `\\=` y `=`, `=..` antes que `=`, `//` antes que `/`, y `**` antes que `*`. Los identificadores se consumen completos antes de clasificarse: `island` y `mod2` son átomos, pero `is` y `mod` aislados son operadores. Un real exige al menos un dígito después del punto; por ello `25.` es `ENTERO(25)` y `PUNTO(.)`. El signo se trata como operador: `-25` es `OP_MENOS` seguido de `ENTERO`.

## 4. Autómata, determinización y minimización

La implementación equivale a un AFD dirigido por el carácter actual:

```text
q0 -- [a-z] --> q_atomo -- C --> q_atomo
q0 -- [A-Z_] --> q_variable -- C --> q_variable
q0 -- [0-9] --> q_entero -- [0-9] --> q_entero
q_entero -- '.' seguido de D --> q_real -- D --> q_real
q0 -- comilla --> q_literal
q0 -- símbolo --> q_simbolo
q0 -- comentario --> q_comentario
```

`q_atomo`, `q_variable`, `q_entero`, `q_real` y los estados de cierre de literal o símbolo son estados de aceptación. Para un AFN de números: `N0 --D--> N1`, `N1 --D--> N1`, `N1 --.--> N2`, `N2 --D--> N3`, `N3 --D--> N3`. La construcción de subconjuntos produce `{N0}`, `{N1}`, `{N2}`, `{N3}` y el estado pozo. `{N1}` acepta enteros y `{N3}` reales; no son equivalentes porque ante `.` tienen transiciones distintas. Los estados sin transición válida se fusionan en el pozo. Agregar al PDF diagramas con estado inicial, aceptación y pozo para números, identificadores y literales.

## 5. Diseño

`Lexer` mantiene posición, línea y columna. `analizar()` delega en `identificador()`, `numero()`, `entre_comillas()` y `comentario_bloque()`. `emitir()` añade tokens y reutiliza una entrada única en la tabla para átomos, variables, números y cadenas. `Resultado` contiene tokens, tabla de lexemas y errores.

## 6. Errores y validación

Se detectan `CARACTER_NO_ADMITIDO`, `NUMERO_MAL_FORMADO`, `ATOMO_SIN_CIERRE`, `CADENA_SIN_CIERRE`, `COMENTARIO_SIN_CIERRE`, `ESCAPE_INVALIDO` y `CONTROL_EN_LITERAL`, incluyendo fragmento, línea y columna. Tras un error recuperable el análisis continúa.

Las pruebas cubren más de veinte casos válidos y más de ocho inválidos, prioridades, límites de tokens, posiciones para `\n`, `\r\n` y `\r`, recuperación y la interfaz CLI. Ejecutar:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q
python3 -m prolog_lexer ejemplos/valido.pl
python3 -m prolog_lexer ejemplos/con_errores.pl
```

## 7. Pendientes para la entrega

- Completar portada, integrantes, conclusiones y referencias académicas.
- Crear y adjuntar los diagramas AFN/AFD solicitados.
- Exportar este documento como `Tarea_JefeGrupo_nombreApellido.pdf`.
- Incluir el enlace del repositorio en el anexo del PDF.
- Verificar que cada integrante tenga una contribución real y pueda explicar el sistema completo.
