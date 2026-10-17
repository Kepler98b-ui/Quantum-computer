# PASO 1: importar las herramientas.
from math import pi  # Permite expresar los ángulos en radianes.
from qiskit import QuantumCircuit, transpile  # Construir y adaptar circuitos.
from qiskit.result import marginal_counts  # Consultar un solo bit del resultado.
from qiskit_aer import AerSimulator  # Ejecutar la simulación local.

# Alice posee q0 (mensaje) y q1 (auxiliar). Bob posee q2 (receptor).
# c0 y c1 guardarán las mediciones de Alice.
# Reservamos c2 para comprobar después el estado de Bob.
circuito = QuantumCircuit(3, 3)

# PASO 2: preparar en q0 el estado que queremos transferir.
# RY ajusta las amplitudes y RZ introduce una fase relativa.
# Elegimos un estado más general que |0>, |1> o |+>.
theta = pi / 3
phi = pi / 4
circuito.ry(theta, 0)
circuito.rz(phi, 0)

# Conocemos estos ángulos para verificar nuestro ejemplo.
# El protocolo de teleportación funciona sin conocerlos.

# PASO 3: compartir un par de Bell entre Alice y Bob.
# H sobre q1 y CNOT hacia q2 preparan:
# (|00> + |11>) / sqrt(2).
# Alice conserva q1 y Bob posee q2.
circuito.h(1)
circuito.cx(1, 2)
circuito.barrier()  # Separador visual; no modifica el estado.

# PASO 4: Alice combina el mensaje con su mitad del par de Bell.
# Estas puertas permiten efectuar una medición en la base de Bell
# mediante mediciones habituales en la base computacional.
circuito.cx(0, 1)
circuito.h(0)

# Alice mide sus dos cúbits y obtiene dos bits clásicos.
# El resultado de q0 se guarda en c0, y el de q1 en c1.
circuito.measure(0, 0)
circuito.measure(1, 1)

# PASO 5: Bob recibe los dos bits clásicos de Alice.
# Según esos bits, su estado necesita ciertas correcciones.
# Los bits indican qué corregir; no contienen las amplitudes del estado.

# Si c1 vale 1, Bob aplica X para intercambiar |0> y |1>.
# if_test evalúa esta condición durante la ejecución del circuito.
# La línea indentada se ejecuta únicamente cuando se cumple la condición.
with circuito.if_test((circuito.clbits[1], 1)):
    circuito.x(2)

# Si c0 vale 1, Bob aplica Z para corregir una fase relativa.
# Cuando ambos bits valen 1, se aplica primero X y después Z.
with circuito.if_test((circuito.clbits[0], 1)):
    circuito.z(2)

# Ahora q2 contiene el estado que inicialmente tenía q0.
# La medición de Alice consume el estado original: no se crea una copia.
# Bob necesita recibir los bits por un canal clásico para corregir su estado.
# Por eso, el protocolo no permite comunicación instantánea.

# PASO 6: verificar la transferencia en una copia del circuito.
# Esta comprobación es adicional al protocolo.
comprobacion = circuito.copy()
comprobacion.barrier()

# Deshacemos en Bob las rotaciones de preparación, en orden inverso.
# Si recibió correctamente el estado, volverá a |0>.
# Esta prueba es sensible tanto a las amplitudes como a la fase.
# Aquí sí necesitamos los ángulos, porque comprobamos un estado conocido.
comprobacion.rz(-phi, 2)
comprobacion.ry(-theta, 2)

# Medimos el resultado de la comprobación y lo guardamos en c2.
comprobacion.measure(2, 2)

# PASO 7: simular 1024 repeticiones completas del experimento.
# AerSimulator funciona sin ruido salvo que configuremos uno.
simulador = AerSimulator()

# Adaptamos el circuito a las instrucciones que admite el simulador.
compilado = transpile(comprobacion, simulador)

# Ejecutamos y esperamos los resultados.
resultado = simulador.run(compilado, shots=1024).result()
conteos = resultado.get_counts()

# Qiskit muestra los bits en el orden c2 c1 c0.
# El primero es la comprobación de Bob; los otros dos pertenecen a Alice.
print("Resultados completos (c2 c1 c0):", conteos)

# Extraemos únicamente el bit c2 para facilitar la interpretación.
conteos_bob = marginal_counts(conteos, indices=[2])
print("Comprobación de Bob:", conteos_bob)
print("Resultado ideal esperado: {'0': 1024}")