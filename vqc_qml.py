"""Clasificador cuántico variacional de dos cúbits, ejecutado localmente."""

from pathlib import Path  # Construye la ruta del gráfico junto a este archivo.
import numpy as np  # Manipula puntos, ángulos y matrices numéricas.
import matplotlib.pyplot as plt  # Dibuja la frontera y la pérdida del entrenamiento.
from sklearn.datasets import make_blobs  # Genera dos nubes con etiquetas conocidas.
from sklearn.model_selection import train_test_split  # Reserva datos para evaluar.
from sklearn.preprocessing import MinMaxScaler  # Convierte coordenadas en ángulos.
from sklearn.metrics import accuracy_score  # Calcula la proporción de aciertos.
from qiskit.circuit.library import zz_feature_map, real_amplitudes  # API actual.
from qiskit.primitives import StatevectorSampler  # Simulador local con interfaz V2.
from qiskit_machine_learning.algorithms.classifiers import VQC  # Modelo híbrido.
from qiskit_machine_learning.optimizers import COBYLA  # Optimizador clásico.

SEMILLA = 42  # Hace reproducibles los datos y las elecciones aleatorias.
NUM_DATOS = 80  # Usamos pocos ejemplos para que el entrenamiento sea manejable.
SHOTS = 1024  # Repeticiones de medición por punto y por conjunto de parámetros.
MAX_EVALUACIONES = 100  # Presupuesto de evaluaciones de la pérdida para COBYLA.


def preparar_datos():
    """Genera los datos y ajusta el escalador exclusivamente con entrenamiento."""

    # Cada fila tiene dos características clásicas; cada etiqueta es 0 o 1.
    datos, etiquetas = make_blobs(
        n_samples=NUM_DATOS,  # Cantidad total de puntos.
        centers=[[-1.0, -1.0], [1.0, 1.0]],  # Centro de cada nube.
        cluster_std=0.45,  # Dispersión alrededor de los centros.
        random_state=SEMILLA,  # Permite repetir la misma generación.
    )

    # Separamos antes de ajustar cualquier transformación: evitamos fuga de datos.
    x_train, x_test, y_train, y_test = train_test_split(
        datos, etiquetas,  # Coordenadas y etiquetas se separan conjuntamente.
        test_size=0.25,  # Reservamos el 25 % para la evaluación final.
        stratify=etiquetas,  # Conservamos la proporción de ambas clases.
        random_state=SEMILLA,  # Mantiene fija la partición del experimento.
    )

    # Un intervalo angular moderado reduce vueltas innecesarias de las rotaciones.
    escalador = MinMaxScaler(feature_range=(0.0, np.pi / 2))

    # Aprende mínimos y máximos sin observar los datos reservados para prueba.
    escalador.fit(x_train)

    # Conservamos también las coordenadas originales para dibujar los puntos.
    return x_train, x_test, y_train, y_test, escalador


def interpretar_medicion(resultado):
    """Agrupa los cuatro resultados de dos cúbits en dos clases."""

    # Cuenta los unos: 00 y 11 tienen paridad par; 01 y 10, impar.
    # Sumaremos las probabilidades de los resultados asignados a cada clase.
    return int(resultado).bit_count() % 2  # Par -> clase 0; impar -> clase 1.


def crear_modelo(historial):
    """Construye la codificación, el circuito entrenable y el optimizador."""

    # El mapa usa H para crear superposición y fases Z/ZZ dependientes de los datos.
    # ZZ introduce dependencia conjunta de las características y puede entrelazar.
    # Sus parámetros x son entradas: NO son los pesos que aprende el optimizador.
    mapa = zz_feature_map(feature_dimension=2, reps=1)

    # El ansatz aplica rotaciones RY ajustables y puertas CX entre los dos cúbits.
    # Con reps=2 hay tres capas RY: dos ángulos por capa, seis pesos en total.
    # Estos pesos son ángulos de puertas; la analogía con neuronas es conceptual.
    ansatz = real_amplitudes(
        num_qubits=2,  # Un cúbit por característica en este ejemplo.
        reps=2,  # Dos bloques de entrelazamiento y una capa RY final.
        entanglement="linear",  # Conecta los cúbits mediante puertas CX.
    )

    # Simula estados sin ruido de hardware, pero estima probabilidades con shots.
    muestreador = StatevectorSampler(default_shots=SHOTS, seed=SEMILLA)

    # Creamos un generador local para elegir pesos iniciales reproducibles.
    generador = np.random.default_rng(SEMILLA)

    # Cada parámetro empieza con un ángulo aleatorio entre -pi y pi radianes.
    inicial = generador.uniform(-np.pi, np.pi, ansatz.num_parameters)

    def registrar_progreso(pesos, perdida):
        # VQC llama esta función al evaluar los pesos propuestos por COBYLA.
        # La entropía cruzada penaliza dar poca probabilidad a la clase correcta.
        historial.append(float(perdida))  # Conserva la pérdida, NO la accuracy.

        # Una evaluación calcula qué tan buenos son unos pesos determinados.
        evaluacion = len(historial)

        # Mostramos avances periódicos para saber que el programa sigue trabajando.
        if evaluacion == 1 or evaluacion % 10 == 0:
            print(
                f"Evaluación {evaluacion:3d}: pérdida = {perdida:.4f}",
                flush=True,
            )

    # COBYLA propone nuevos ángulos sin calcular derivadas del circuito.
    # Cada propuesta se evalúa con los datos de entrenamiento y sus etiquetas.
    # Busca reducir la pérdida; los intentos intermedios pueden empeorarla.
    optimizador = COBYLA(maxiter=MAX_EVALUACIONES)

    # VQC conecta el circuito cuántico con el entrenamiento clásico.
    modelo = VQC(
        feature_map=mapa,  # Primero codifica cada punto clásico en dos cúbits.
        ansatz=ansatz,  # Transforma el estado usando los pesos entrenables.
        sampler=muestreador,  # Obtiene frecuencias de medición en el simulador.
        optimizer=optimizador,  # Decide qué pesos probar a continuación.
        initial_point=inicial,  # Punto de partida del entrenamiento.
        loss="cross_entropy",  # Compara probabilidades y etiquetas correctas.
        interpret=interpretar_medicion,  # Agrupa mediciones por paridad.
        output_shape=2,  # Produce una probabilidad para cada clase.
        callback=registrar_progreso,  # Informa del avance en la terminal.
    )

    # Mostramos el tamaño del circuito entrenable.
    print(f"Modelo: 2 cúbits y {ansatz.num_parameters} parámetros entrenables.")

    # El clasificador ya está construido, pero todavía no ha aprendido.
    return modelo


def graficar(modelo, escalador, x_train, x_test, y_train, y_test, historial):
    """Dibuja la probabilidad de clase 1 y la pérdida del entrenamiento."""

    # Combinamos coordenadas solo para elegir los límites visuales del gráfico.
    puntos = np.vstack((x_train, x_test))

    # Añadimos márgenes alrededor de los puntos para mostrar la frontera.
    inferior = puntos.min(axis=0) - 0.4
    superior = puntos.max(axis=0) + 0.4

    # Construimos una cuadrícula de 40 por 40 posiciones.
    xx, yy = np.meshgrid(
        np.linspace(inferior[0], superior[0], 40),  # Coordenadas horizontales.
        np.linspace(inferior[1], superior[1], 40),  # Coordenadas verticales.
    )

    # Convertimos la cuadrícula en una lista de puntos con dos características.
    malla = np.column_stack((xx.ravel(), yy.ravel()))

    # Reutilizamos la escala aprendida con entrenamiento; no volvemos a ajustarla.
    malla_escalada = escalador.transform(malla)

    # Predecir muchos puntos también requiere ejecutar el circuito.
    print("Calculando la frontera de decisión...", flush=True)

    # El modelo calcula probabilidades usando los pesos ya entrenados.
    probabilidades = modelo.predict_proba(malla_escalada)

    # La columna 1 corresponde a la probabilidad estimada de la clase 1.
    p1 = probabilidades[:, 1].reshape(xx.shape)

    # Creamos dos paneles: frontera de decisión y evolución de la pérdida.
    figura, ejes = plt.subplots(1, 2, figsize=(12, 5))

    # El fondo representa la probabilidad de clase 1 en cada posición.
    fondo = ejes[0].contourf(
        xx, yy, p1,  # Coordenadas originales y probabilidades estimadas.
        levels=np.linspace(0, 1, 11),  # Divide el intervalo de probabilidades.
        cmap="coolwarm",  # Azul: menor probabilidad; rojo: mayor probabilidad.
        alpha=0.7,  # Suaviza el color para poder ver los puntos.
    )

    # La frontera está donde ambas clases tienen la misma probabilidad.
    if p1.min() < 0.5 < p1.max():
        ejes[0].contour(
            xx, yy, p1,
            levels=[0.5],  # Dibuja la línea P(clase 1) = 0.5.
            colors="black",
            linewidths=1.5,
        )

    # Los círculos representan datos usados para entrenar.
    ejes[0].scatter(
        x_train[:, 0], x_train[:, 1],
        c=y_train,  # El color indica la etiqueta real, no la predicción.
        cmap="coolwarm", vmin=0, vmax=1,
        edgecolors="black", marker="o", s=35,
        label="Entrenamiento",
    )

    # Los triángulos representan datos reservados para evaluar.
    ejes[0].scatter(
        x_test[:, 0], x_test[:, 1],
        c=y_test,  # Azul corresponde a clase 0; rojo, a clase 1.
        cmap="coolwarm", vmin=0, vmax=1,
        edgecolors="black", marker="^", s=80,
        label="Prueba",
    )

    # Añadimos las etiquetas del primer panel.
    ejes[0].set_title("VQC: frontera de decisión (P(clase 1) = 0.5)")
    ejes[0].set_xlabel("Característica 1")
    ejes[0].set_ylabel("Característica 2")
    ejes[0].legend()

    # La barra permite interpretar numéricamente el color del fondo.
    figura.colorbar(
        fondo,
        ax=ejes[0],
        label="Probabilidad estimada de clase 1",
    )

    # Una curva irregular es normal: COBYLA explora y hay muestreo finito.
    ejes[1].plot(
        range(1, len(historial) + 1),
        historial,
        color="purple",
    )

    # La pérdida mide el objetivo del entrenamiento; no es el porcentaje de error.
    ejes[1].set_title("Entrenamiento clásico-cuántico")
    ejes[1].set_xlabel("Evaluación de la función objetivo")
    ejes[1].set_ylabel("Pérdida: entropía cruzada")
    ejes[1].grid(alpha=0.3)

    # Acomodamos las etiquetas para que no se superpongan.
    figura.tight_layout()

    # Guardamos la imagen junto al script, independientemente de la terminal.
    ruta = Path(__file__).with_name("vqc_resultados.png")
    figura.savefig(ruta, dpi=150)
    print(f"Gráfico guardado en: {ruta}")

    # Abre la ventana; ciérrala para que el programa termine.
    plt.show()


def main():
    """Ejecuta generación, entrenamiento, evaluación y visualización."""

    # Generamos datos, particiones y un escalador ajustado solo con entrenamiento.
    x_train, x_test, y_train, y_test, escalador = preparar_datos()

    # Convertimos las características de entrenamiento en entradas angulares.
    train_escalado = escalador.transform(x_train)

    # Aplicamos exactamente la misma transformación a los datos de prueba.
    test_escalado = escalador.transform(x_test)

    # Esta lista guardará las pérdidas evaluadas durante la optimización.
    historial = []

    # Construimos el modelo cuántico y su optimizador clásico.
    modelo = crear_modelo(historial)

    # Informamos de cuántos ejemplos tiene cada partición.
    print(f"Datos: {len(y_train)} de entrenamiento y {len(y_test)} de prueba.")
    print("Entrenando el VQC; espera los mensajes de progreso...", flush=True)

    # El ciclo híbrido ajusta los pesos únicamente con los datos de entrenamiento.
    # Para cada propuesta: codifica -> aplica ansatz -> mide -> calcula pérdida.
    # COBYLA utiliza esa pérdida para buscar la siguiente propuesta de pesos.
    modelo.fit(train_escalado, y_train)

    # Con los pesos aprendidos, predecimos la clase más probable de cada punto.
    pred_train = modelo.predict(train_escalado)
    pred_test = modelo.predict(test_escalado)

    # La accuracy de entrenamiento describe el ajuste sobre ejemplos conocidos.
    acierto_train = accuracy_score(y_train, pred_train)

    # La accuracy de prueba evalúa ejemplos que no participaron en el aprendizaje.
    acierto_test = accuracy_score(y_test, pred_test)

    # Mostramos porcentajes de aciertos y ángulos finales del circuito.
    print(f"Accuracy de entrenamiento: {acierto_train:.2%}")
    print(f"Accuracy de prueba:        {acierto_test:.2%}")
    print("Pesos finales (radianes):", np.round(modelo.weights, 3))

    # Dibujamos la respuesta del clasificador y la evolución del entrenamiento.
    graficar(modelo, escalador, x_train, x_test, y_train, y_test, historial)


# Esta condición evita entrenar automáticamente si otro archivo importa el módulo.
if __name__ == "__main__":
    main()  # Inicia el experimento cuando ejecutas directamente este archivo.