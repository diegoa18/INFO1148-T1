% Hechos
padre(juan, ana).
padre(juan, pedro).

% Regla
abuelo(X, Z) :- padre(X, Y), padre(Y, Z).

/* Consulta */
?- abuelo(juan, Quien).

mensaje("Hola\n").
persona('Juan Pérez').
calculo(X) :- X is 3.14 + 2 * 5.
lista([a, b | Resto]).
