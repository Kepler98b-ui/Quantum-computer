# Importamos la herramienta para construir el circuito cuántico.
from qiskit import QuantumCircuit

# Importamos el simulador local; el experimento se ejecutará en tu computadora.
from qiskit_aer import AerSimulator

# Importamos las herramientas de gráficos con el nombre abreviado "plt".
import matplotlib.pyplot as plt

# Creamos un cúbit, inicialmente en |0>, y un bit clásico para la medición.
circuito = QuantumCircuit(1, 1)

# Aplicamos Hadamard al cúbit 0 para preparar (|0> + |1>) / sqrt(2).
# Al medir en la base computacional, 0 y 1 tienen igual probabilidad.
circuito.h(0)

# Añadimos la medición del cúbit 0 y guardamos su resultado en el bit clásico 0.
# La medición ideal proyecta el estado a |0> o |1>.
circuito.measure(0, 0)

# Creamos el simulador ideal, sin ruido configurado.
simulador = AerSimulator()

# Ejecutamos 1024 repeticiones independientes: preparar |0>, aplicar H y medir.
# .result() espera a que finalice la simulación y obtiene sus resultados.
resultado = simulador.run(circuito, shots=1024).result()

# Obtenemos un diccionario con las frecuencias, por ejemplo {'0': 523, '1': 501}.
conteos = resultado.get_counts()

# Mostramos el dibujo del circuito en la terminal.
print(circuito.draw(output="text"))

# Mostramos las frecuencias obtenidas; sus valores suman 1024.
print("Resultados de las 1024 mediciones:", conteos)

# Creamos una figura y unos ejes donde dibujar las barras.
figura, ejes = plt.subplots(figsize=(7, 5))

# Extraemos las frecuencias en orden: primero 0, después 1.
# .get(clave, 0) devuelve cero si ese resultado no apareció.
frecuencias = [conteos.get("0", 0), conteos.get("1", 0)]

# Dibujamos una barra por resultado; su altura representa el número de veces.
barras = ejes.bar(["0", "1"], frecuencias, color=["royalblue", "darkorange"])

# Identificamos el experimento en el título.
ejes.set_title("Un cúbit con Hadamard — 1024 repeticiones")

# Indicamos qué representa el eje horizontal.
ejes.set_xlabel("Resultado de la medición")

# Indicamos que el eje vertical muestra cantidades, no porcentajes.
ejes.set_ylabel("Frecuencia (número de veces)")

# Dejamos espacio encima de las barras para escribir sus valores.
ejes.set_ylim(0, max(frecuencias) * 1.15)

# Escribimos la frecuencia exacta sobre cada barra.
ejes.bar_label(barras, padding=3)

# Ajustamos los márgenes para que las etiquetas se vean completas.
figura.tight_layout()

# Abrimos la ventana del histograma; el programa espera hasta que la cierres.
plt.show()

# RECORDATORIO DE GIT
# Ejecuta estos comandos en PowerShell, dentro de Quantum-computer.
# Son comentarios: Python no los ejecuta.
#
# git status
# git add primer_circuito.py .gitignore
# git commit -m "Agrega circuito de un cúbit e histograma de 1024 mediciones"
# git push -u origin main