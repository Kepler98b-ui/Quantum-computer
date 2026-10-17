# Quantum Computer

Laboratorio educativo de computación cuántica desarrollado con **Python**, **Qiskit** y **Qiskit Aer**.

Este proyecto explora la superposición, el entrelazamiento, la teletransportación, la búsqueda cuántica y los efectos del ruido mediante simulaciones locales. Los programas incluyen comentarios explicativos y gráficos para facilitar el aprendizaje.

## Experimentos y algoritmos

| Ejercicio | Archivo | Cúbits | Descripción |
|---|---|---:|---|
| Hola Mundo cuántico | [primer_circuito.py](primer_circuito.py) | 1 | Prepara una superposición con Hadamard y muestra los resultados de las mediciones. |
| Estado de Bell | [estado_bell.py](estado_bell.py) | 2 | Prepara un estado entrelazado mediante Hadamard y CNOT. |
| Teletransportación cuántica | [teletransportacion.py](teletransportacion.py) | 3 | Transfiere un estado usando entrelazamiento, dos bits clásicos y correcciones condicionadas. |
| Algoritmo de Grover | [grover_2_qubits.py](grover_2_qubits.py) | 2 | Busca el candidato `11` entre cuatro posibilidades mediante un oráculo y difusión. |
| Ruido cuántico | [bell_con_ruido.py](bell_con_ruido.py) | 2 | Compara un circuito de Bell ideal con otro que incorpora despolarización después de CNOT. |

## Herramientas utilizadas

- **Python 3.12:** lenguaje de programación.
- **Qiskit:** construcción y manipulación de circuitos cuánticos.
- **Qiskit Aer:** simulación local de circuitos ideales y con ruido.
- **Matplotlib:** visualización de los resultados.
- **Git y GitHub:** control de versiones y almacenamiento del proyecto.

Los ejemplos se ejecutan en una computadora convencional. No requieren acceso a hardware cuántico ni credenciales de IBM Quantum.

## Instalación en Windows

### 1. Descargar el repositorio

Con Python y Git instalados, abre PowerShell y ejecuta:

```powershell
git clone https://github.com/Kepler98b-ui/Quantum-computer.git
cd Quantum-computer
```

Si ya descargaste el repositorio, abre una terminal en su carpeta existente.

### 2. Crear el entorno virtual

En la primera instalación, ejecuta:

```powershell
py -3.12 -m venv .venv
```

El entorno virtual mantiene las dependencias del proyecto separadas de otros programas.

### 3. Instalar las dependencias

Utiliza directamente el Python del entorno virtual:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install qiskit qiskit-aer matplotlib
```

Para comprobar la instalación:

```powershell
.\.venv\Scripts\python.exe -c "import qiskit, qiskit_aer, matplotlib; print('Dependencias disponibles')"
```

La carpeta `.venv` está excluida del control de versiones mediante `.gitignore`.

## Ejecutar los programas

Desde la carpeta `Quantum-computer`, elige el comando del ejercicio que quieras ejecutar:

```powershell
# Hola Mundo cuántico
.\.venv\Scripts\python.exe .\primer_circuito.py

# Estado de Bell
.\.venv\Scripts\python.exe .\estado_bell.py

# Teletransportación cuántica
.\.venv\Scripts\python.exe .\teletransportacion.py

# Algoritmo de Grover
.\.venv\Scripts\python.exe .\grover_2_qubits.py

# Comparación con ruido
.\.venv\Scripts\python.exe .\bell_con_ruido.py
```

Los programas que utilizan Matplotlib abren una ventana con el gráfico. Ciérrala para que el programa termine y PowerShell vuelva a aceptar comandos.

Grover guarda `histograma_grover.png` y el experimento de ruido guarda `comparacion_ruido_bell.png` en la carpeta desde la que se ejecutan.

### Activación opcional del entorno virtual

Los comandos anteriores utilizan directamente el Python de `.venv`. También puedes activar el entorno en PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Mientras esté activado, puedes ejecutar un programa así:

```powershell
python .\estado_bell.py
```

Para desactivarlo:

```powershell
deactivate
```

Si PowerShell bloquea la activación, utiliza los comandos con `.\.venv\Scripts\python.exe` indicados anteriormente.

Cerrar la terminal conserva el entorno virtual y las dependencias instaladas.

## Interpretación de los resultados

- **Hola Mundo:** las probabilidades ideales de `0` y `1` son del 50 %. Las frecuencias fluctúan al realizar un número finito de repeticiones.
- **Bell:** en la simulación ideal aparecen `00` y `11`. El histograma muestra las correlaciones esperadas, aunque por sí solo no certifica entrelazamiento.
- **Teletransportación:** la salida `{'0': 1024}` corresponde a una comprobación que deshace la preparación conocida en Bob. Antes de esa comprobación, Bob tiene el estado original de Alice.
- **Grover:** con cuatro candidatos y una única solución marcada, una iteración ideal concentra toda la probabilidad en `11`. Las 1024 repeticiones ejecutan el experimento completo.
- **Ruido:** el modelo utiliza despolarización con `p = 0.20` después de CNOT. Predice probabilidades de 45 %, 5 %, 5 % y 45 % para `00`, `01`, `10` y `11`.

## Alcance del proyecto

Este es un proyecto educativo en desarrollo.

El oráculo de Grover reconoce un candidato definido en el código. En una aplicación, el oráculo implementaría una condición de búsqueda.

El modelo de ruido es didáctico y no representa la calibración de un dispositivo concreto.