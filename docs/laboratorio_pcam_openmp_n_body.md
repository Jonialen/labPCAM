# LABORATORIO PRÁCTICO: COMPUTACIÓN PARALELA Y DISTRIBUIDA
## LABORATORIO PCAM + OPENMP
### PCAM aplicado con OpenMP: Simulación gravitacional N-Body en 2D

---

- **Objetivo:** Diseñar, implementar y evaluar una solución paralela no trivial utilizando la metodología PCAM y OpenMP. El laboratorio debe demostrar decisiones de partición, comunicación, aglomeración y mapeo, además de medir rendimiento y corrección.
- **Nombre:** __________________________________
- **Carné:** ___________________________________
- **Fecha de entrega:** ________________________
- **Modalidad:** Individual

> **Idea central:** No se evaluará únicamente que el programa "use OpenMP". Se evaluará que el diseño paralelo esté justificado con PCAM y que las decisiones puedan comprobarse con mediciones.

---

## 1. Problema a resolver

Construya una simulación N-Body gravitacional en dos dimensiones. Cada cuerpo tiene posición, velocidad y masa. En cada paso de simulación, cada cuerpo recibe la fuerza producida por los demás cuerpos y luego actualiza su velocidad y posición.

```cpp
struct Body {
    double x, y;
    double vx, vy;
    double mass;
};
```

- **Modelo mínimo:** Para cada cuerpo $i$, acumule la fuerza causada por todos los cuerpos $j \neq i$. Luego calcule aceleración, actualice velocidad y posición, y repita durante varios pasos.
- **Carga computacional:** La versión directa realiza aproximadamente $N^2$ interacciones por paso. Esto permite observar speedup, overhead, balanceo de carga y efectos de sincronización de manera medible.

---

## 2. Requisitos técnicos

- **Lenguaje:** C++ (C++17 o superior) con OpenMP.
- El tamaño $N$ y el número de pasos deben ser configurables por argumentos de línea de comandos.
- Use una semilla fija ($\text{seed} = 42$) para generar las mismas condiciones iniciales en todas las versiones.
- Mida tiempos con `omp_get_wtime()`. No use tiempos impresos manualmente ni estimaciones.
- La misma entrada debe utilizarse al comparar versiones secuenciales y paralelas.
- El programa debe imprimir un resumen reproducible al finalizar cada ejecución.

### Ejemplo de compilación
```bash
g++ -O2 -std=c++17 -fopenmp nbody.cpp -o nbody
```

### Salida mínima esperada
```text
Student: Nombre Apellido
Mode: parallel-optimized
N: 5000 | Steps: 10 | Threads: 8
Schedule: dynamic | Chunk: 32
Elapsed: 1.842 s
Checksum: 12753.381920
```

- **Escala sugerida:** Use $N = 5000$ y 10 pasos como punto de partida. Si su equipo tarda demasiado o demasiado poco, ajuste $N$ de forma razonable, pero use exactamente el mismo valor en todas las comparaciones y documente el cambio.

---

## 3. Implementaciones obligatorias

| Versión | Descripción | Objetivo | Archivo sugerido |
| :--- | :--- | :--- | :--- |
| **A** | Secuencial, doble ciclo completo $i \times j$. | Baseline de corrección y tiempo. | `nbody_seq.cpp` |
| **B** | Paralela directa: cada cuerpo $i$ acumula su propia fuerza. | Aplicar PCAM y OpenMP sin introducir carreras. | `nbody_parallel.cpp` |
| **C** | Optimizada: explotar la simetría de pares $(i, j)$ una sola vez. | Reducir trabajo y resolver la concurrencia correctamente. | `nbody_optimized.cpp` |

> **Versión C - Condición importante:** Al calcular una pareja solo una vez, una interacción puede modificar acumuladores asociados a dos cuerpos. Debe identificar y resolver correctamente cualquier *race condition*. Puede investigar estrategias con `atomic`, `critical` o acumuladores privados por thread; justifique su elección.

---

## 4. Diseño obligatorio con PCAM

Antes de mostrar resultados de rendimiento, documente sus decisiones de diseño. No copie definiciones: aplíquelas específicamente a su simulación.

| Etapa | Pregunta que debe responder | Evidencia técnica esperada |
| :--- | :--- | :--- |
| **P - Partition** | ¿Cuál es la unidad de trabajo paralelizable? ¿Qué dependencias existen entre pasos? | Explique cómo divide cuerpos/interacciones y por qué el cálculo puede ejecutarse en paralelo. |
| **C - Communication** | ¿Qué datos son compartidos? ¿Qué resultados deben combinarse o sincronizarse? | Identifique lecturas compartidas, escrituras y puntos con riesgo de carrera. |
| **A - Agglomeration** | ¿Qué tareas pequeñas conviene agrupar para que el overhead no domine? | Compare al menos tres *chunk sizes* y relacione granularidad con tiempo. |
| **M - Mapping** | ¿Cómo se asigna el trabajo a los threads? | Compare `static`, `dynamic` y `guided`; analice *load balancing* y costo de *scheduling*. |

---

## 5. Experimentos obligatorios

Realice varias ejecuciones y registre cada resultado en `results.csv`. Ejecute cada configuración al menos 3 veces y reporte el promedio. Mantenga $N$, pasos y seed constantes.

| Threads | Schedule | Chunk | Tiempo promedio | Speedup / Efficiency |
| :---: | :---: | :---: | :---: | :---: |
| 1 | sequential | — | | |
| 2 | static | default | | |
| 4 | static | default | | |
| 8 | static | default | | |
| 8 | static | 8 | | |
| 8 | static | 64 | | |
| 8 | dynamic | 8 | | |
| 8 | dynamic | 64 | | |
| 8 | guided | default | | |

- **Cálculos requeridos:**
  - **Speedup:** $S(p) = \frac{T_1}{T_p}$
  - **Efficiency:** $E(p) = \frac{S(p)}{p}$
- Compare también la versión paralela directa contra la versión optimizada por pares.

---

## 6. Evidencia de ejecución obligatoria

> **Importante:** La entrega debe incluir evidencia verificable de que el software fue compilado y ejecutado. Una captura del código fuente **no cuenta** como evidencia de ejecución.

Incluya dentro del informe las siguientes capturas de pantalla, y adjunte los archivos originales en la carpeta `evidence/`:

1. **Evidencia 1 - Compilación exitosa:** Terminal mostrando el comando de compilación y sin errores.
2. **Evidencia 2 - Ejecución secuencial:** Debe verse $N$, pasos, tiempo y checksum.
3. **Evidencia 3 - Ejecución paralela:** Debe verse número real de threads, schedule, chunk, tiempo y checksum.
4. **Evidencia 4 - Ejecución optimizada:** Salida equivalente para la versión que explota la simetría de pares.
5. **Evidencia 5 - Resumen de hardware:** El programa debe imprimir `omp_get_num_procs()` y `omp_get_max_threads()` (o equivalente claramente documentado).

### Formato de evidencia
```text
Student: Nombre Apellido
Executable: ./nbody
Mode: parallel
N: 5000 | Steps: 10 | Seed: 42
Threads requested: 8 | Threads used: 8
Schedule: dynamic | Chunk: 64
Elapsed: 1.842 s
Checksum: 12753.381920
Processors reported by OpenMP: 8
```

- **Corrección numérica:** Con la misma seed y parámetros, compare los resultados de las versiones. Reporte un checksum y la diferencia máxima observada respecto a la versión secuencial. Pequeñas diferencias de punto flotante son aceptables si están explicadas; resultados físicamente divergentes no lo son.

---

## 7. Entregables

Estructura de entrega esperada:

```text
lab-pcam-nbody/
├── src/
│   ├── nbody_seq.cpp
│   ├── nbody_parallel.cpp
│   └── nbody_optimized.cpp
├── evidence/
│   ├── compile.png
│   ├── sequential.png
│   ├── parallel.png
│   ├── optimized.png
│   └── hardware.png
├── results.csv
├── README.md
└── report.pdf
```

- **Reporte (`report.pdf`):** Debe tener entre **3 y 5 páginas** (sin contar anexos) e incluir:
  - Diseño PCAM
  - Estrategia OpenMP
  - Resultados experimentales
  - Speedup / Efficiency
  - Análisis de *race conditions*
  - Evidencia
  - Conclusiones

---

## 8. Preguntas de análisis

1. ¿Cuál fue la unidad mínima de trabajo paralelizable y por qué no necesariamente conviene usarla como una tarea individual?
2. ¿Qué información es compartida entre threads? Identifique cuáles accesos son solo lectura y cuáles requieren protección.
3. ¿Qué efecto tuvo el *chunk size* sobre el rendimiento? Relaciónelo con *Agglomeration*.
4. Compare `static`, `dynamic` y `guided`. ¿Cuál funcionó mejor en su caso y qué evidencia respalda su conclusión?
5. ¿Qué *race condition* aparece al calcular cada pareja $(i, j)$ una sola vez? ¿Cómo la resolvió?
6. ¿La versión con menos operaciones fue siempre la más rápida? Explique usando overhead y sincronización.
7. Reporte *Speedup* y *Efficiency* para 2, 4 y 8 threads. ¿Dónde dejó de escalar linealmente?
8. Si tuviera 64 cores, ¿esperaría 8 veces el rendimiento obtenido con 8 threads? Justifique con sus mediciones.

---

## 9. Rúbrica de evaluación

| Componente | Puntos | Criterio |
| :--- | :---: | :--- |
| **Versión secuencial** | 10 | Correcta, reproducible y usada como baseline. |
| **Diseño PCAM** | 20 | P, C, A y M aplicados al problema y justificados. |
| **Paralelización OpenMP** | 15 | Uso correcto de threads, scheduling y mediciones. |
| **Optimización y concurrencia** | 20 | Simetría de pares + solución correcta de race conditions. |
| **Experimentos** | 15 | Datos suficientes, repeticiones, speedup y efficiency. |
| **Evidencia de ejecución** | 10 | Capturas completas, legibles y coherentes con `results.csv`. |
| **Informe y conclusiones** | 10 | Análisis técnico, claridad y conclusiones basadas en resultados. |
| **Total** | **100** | |

> **Criterio de cierre:** El objetivo no es encontrar "el pragma correcto", sino demostrar que puede diseñar una solución paralela, medirla y defender sus decisiones con PCAM.