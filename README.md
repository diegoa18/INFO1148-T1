# Analizador léxico de Prolog — INFO1148

Implementación en Python de un analizador léxico para el subconjunto de Prolog de la tarea. Reconoce tokens, conserva línea y columna, registra lexemas sin duplicados y continúa después de errores recuperables. No realiza análisis sintáctico ni semántico.

## Requisitos

- Python 3.10 o superior.
- `pytest` solamente para ejecutar las pruebas.

## Ejecutar el analizador

Desde la raíz del repositorio:

```bash
python3 -m prolog_lexer ejemplos/valido.pl
```

Para ver diagnósticos y recuperación ante errores:

```bash
python3 -m prolog_lexer ejemplos/con_errores.pl
```

La salida estándar contiene `TOKENS` y `TABLA DE LEXEMAS`. Los errores se escriben en la salida de error. El proceso termina con código `0` si no hay errores léxicos, `1` si los hay y `2` si no se pudo leer el archivo.

## Pruebas

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q
```

## Estructura

- `prolog_lexer/lexer.py`: reconocimiento y recuperación de errores.
- `prolog_lexer/modelos.py`: modelos de token, error, tabla y resultado.
- `prolog_lexer/__main__.py`: interfaz de línea de comandos.
- `tests/`: pruebas unitarias, de prioridades, posiciones y CLI.
- `ejemplos/`: una entrada válida y otra con errores recuperables.
- `docs/informe_tecnico.md`: material base para el informe entregable.
