
import os
import graphviz

def generar_grafo_completo(
    transiciones: list[tuple[str, str, str]], 
    lexema: str, 
    tipo_token: str, 
    nombre_archivo: str,
    nombre_unico: str
) -> None:
    """
    Construye y guarda una única imagen nítida con el camino recorrido por el AFD
    exclusivamente para la entrada de este lexema.
    """
    dot = graphviz.Digraph(nombre_archivo, format="png")
    
    # Alta resolución (DPI=300) y orientación de izquierda a derecha
    dot.attr(rankdir="LR", dpi="300")
    dot.attr(
        label=f"Token: {tipo_token} | Lexema: {repr(lexema)}", 
        labelloc="t", 
        fontsize="12", 
        fontname="Helvetica-Bold"
    )

    dot.attr("node", shape="circle", style="filled", fillcolor="#FFFFFF", fontname="Helvetica")
    dot.attr("edge", fontname="Courier", fontsize="10")

    # Identificar el estado final del recorrido
    estado_final = transiciones[-1][2]

    # Conjunto de todos los estados involucrados en este lexema
    estados_unicos = set()
    for origen, _, destino in transiciones:
        estados_unicos.add(origen)
        estados_unicos.add(destino)

    # Dibujar nodos
    for estado in estados_unicos:
        if estado == "q0":
            dot.node(estado, label="q0\n(Inicio)", fillcolor="#CCE5FF", color="#004085")
        elif estado == estado_final:
            # Estado de aceptación con doble círculo verde
            dot.node(estado, label=estado, shape="doublecircle", fillcolor="#D4EDDA", color="#28A745")
        else:
            dot.node(estado, label=estado)

    # Dibujar aristas de las transiciones acumuladas
    for origen, simbolo, destino in transiciones:
        dot.edge(origen, destino, label=f" {simbolo} ", color="#0056B3", penwidth="1.5")

    # Renderizar imagen (genera archivo grafo_1.png, grafo_2.png, etc.)
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    carpeta_grafos = os.path.join(ruta_actual, "grafos")
    ruta_salida = os.path.join(carpeta_grafos, f"{nombre_archivo}_{nombre_unico}")
    dot.render(ruta_salida, cleanup=True)