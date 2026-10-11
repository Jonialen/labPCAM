# Metodología PCAM (Parallel Computation Abstract Machine)

> *"Diseñar el paralelismo antes de escribir el código."*  
> **PCAM no ejecuta el programa. PCAM ayuda a diseñarlo.**

La metodología PCAM responde a tres preguntas fundamentales en computación paralela:
* ¿Qué paralelizar?
* ¿Cuánto paralelizar?
* ¿Dónde ejecutarlo?

---

## Estructura General de la Metodología

```
  [P] PARTITION       --> Dividir
        │
  [C] COMMUNICATION   --> Conectar
        │
  [A] AGGLOMERATION   --> Agrupar
        │
  [M] MAPPING         --> Asignar
```

---

## Hilo Conductor: El Problema de los 1,000 Libros

Este problema sirve como guía práctica para ver evolucionar un diseño paralelo a través de cada etapa de PCAM:

* **📚 1,000 Libros:** El trabajo total a realizar.
* **🎓 8 Estudiantes:** Los recursos disponibles (trabajadores en paralelo).
* **🏫 1 Destino:** El salón al que deben llegar todos los libros.

**Objetivo:** Organizar este trabajo de forma eficiente utilizando las 4 etapas de PCAM.

---

## Etapa 1: P — Partition (Dividir)

**Pregunta clave:** *¿Cómo dividimos el trabajo?*

### 1. La idea inicial
* Considerar: **$1 \text{ libro} = 1 \text{ tarea}$**.
* Se obtienen $1,000$ tareas independientes que en teoría pueden realizarse en paralelo:
  ```
  [📚][📚][📚][📚][📚][📚][📚][📚] ... × 1,000
  ```
* Cada libro se concibe como una unidad de trabajo independiente.
* También se podría dividir por estantes, zonas del salón o grupos de libros.

### 2. ¿Qué identifica Partition?
* Todo el trabajo que **PUEDE** dividirse.
* Las unidades mínimas de trabajo independiente.
* El paralelismo potencial máximo.

> *Partition identifica todo el trabajo que puede dividirse.*

### 3. Estrategias de partición
Existen dos enfoques principales según el problema:

1. **Data Partitioning (Partición por Datos):**
   * Dividir según los datos (en este caso, los libros o conjuntos de datos).
2. **Functional Partitioning (Partición Funcional):**
   * Dividir según las fases o tareas a realizar:
     * **Recoger:** Recoger libros del estante.
     * **Transportar:** Transportar libros al pasillo.
     * **Ordenar:** Ordenar libros en destino.
     * **Verificar:** Verificar que llegaron todos.

*Ambas estrategias son válidas; la elección depende del problema en cuestión.*

---

## Etapa 2: C — Communication (Conectar)

> *"Los estudiantes eventualmente necesitan coordinar. Cada uno traslada libros, pero alguien debe saber cuántos han llegado al destino."*

**Pregunta clave:** *Communication permite coordinar y combinar información entre las tareas.*

### 1. ¿Qué información comparten los trabajadores?
* **Progreso individual:** Cuántos libros ha trasladado cada estudiante.
* **Trabajo restante:** Cuánto trabajo falta por completar.
* **Verificación total:** Si los $1,000$ libros llegaron exitosamente al destino.

### 2. Esquema de consolidación (Coordinador Central)
Los resultados individuales se combinan para obtener el total global:

* Estudiante 1 $\rightarrow$ 150 libros
* Estudiante 2 $\rightarrow$ 100 libros
* Estudiante 3 $\rightarrow$ 200 libros
* Estudiante 4 $\rightarrow$ 125 libros
* Estudiante 5 $\rightarrow$ 125 libros
* Estudiante 6 $\rightarrow$ 100 libros
* Estudiante 7 $\rightarrow$ 100 libros
* Estudiante 8 $\rightarrow$ 100 libros
* **TOTAL:** $1,000\text{ libros } \checkmark$

---

## Etapa 3: A — Agglomeration (Agrupar)

**Pregunta clave:** *¿Tiene sentido administrar 1,000 libros como 1,000 tareas individuales?*

### 1. El problema con 1,000 tareas individuales
* Transportar y administrar cada libro individualmente genera demasiado **overhead**.
* Coordinar $1,000$ tareas resulta más costoso que el trabajo físico en sí.
* Los estudiantes perderían tiempo reportando y gestionando libro por libro.

```
SIN AGGLOMERATION:
📚 📚 📚 📚 📚 📚 📚 📚 ... × 1,000
(1,000 tareas individuales = Overhead excesivo)
```

### 2. La solución: Agrupar en cajas
* $1,000\text{ libros} \longrightarrow 20\text{ cajas de } 50\text{ libros} \longrightarrow 20\text{ tareas en lugar de } 1,000$.

```
CON AGGLOMERATION:
📦 CAJA   📦 CAJA   📦 CAJA   📦 CAJA ... × 20
(Menos tareas que administrar, mismo trabajo total)
```

> *Partition identifica todo lo que podría hacerse en paralelo. Agglomeration agrupa ese trabajo en unidades prácticas y eficientes.*

### 3. Granularidad (Granularity Trade-off)

| Tipo | Esquema | Características | Pros / Contras |
| :--- | :--- | :--- | :--- |
| **Fine-Grained** (Grano fino) | `[ ][ ][ ][ ][ ][ ][ ]` | Muchas tareas pequeñas | $\checkmark$ Más paralelismo<br>$\times$ Más overhead |
| **Coarse-Grained** (Grano grueso) | `[      ][      ][      ]` | Menos tareas, más grandes | $\checkmark$ Menos overhead<br>$\times$ Menos paralelismo |

> **Trade-off:** El diseñador debe encontrar el punto óptimo entre paralelismo y costo de administración.  
> *"Más tareas no siempre significa más velocidad."*

---

## Etapa 4: M — Mapping (Asignar)

**Pregunta clave:** *¿Quién transporta cada caja? (Tenemos 20 cajas y 8 estudiantes).*

> *"Un estudiante esperando mientras otro sigue trabajando representa recursos desperdiciados (tiempo IDLE)."*

### 1. Comparación de Mapeos

* **Bad Mapping $\times$ (Sin balanceo):**
  * Estudiante 1: 8 cajas (mucho tiempo)
  * Estudiante 2: 2 cajas (poco tiempo $\rightarrow$ **IDLE**)
  * Estudiante 3: 2 cajas (poco tiempo $\rightarrow$ **IDLE**)
  * Estudiantes 4 al 8: 1 caja c/u (mínimo tiempo $\rightarrow$ **IDLE**)
  * *Resultado:* La mayoría termina rápido y queda esperando al primero.

* **Better Mapping $\checkmark$ (Con Load Balancing):**
  * Estudiantes 1 al 4: 3 cajas cada uno.
  * Estudiantes 5 al 8: 2 cajas cada uno.
  * *Resultado:* Carga equitativa, tiempo equilibrado y **Makespan reducido**.

### 2. Static vs. Dynamic Mapping

```
STATIC MAPPING (schedule: static)
─────────────────────────────────────────────────────────────
Las cajas se asignan ANTES de empezar.
  Estudiante 1 ──> Cajas 1, 2, 3
  Estudiante 2 ──> Cajas 4, 5, 6
  Estudiante 3 ──> Cajas 7, 8, 9
  Estudiante 4 ──> Cajas 10, 11, 12
✓ Ideal cuando todas las cajas requieren esfuerzo uniforme.
✓ Bajo overhead de scheduling.
```

```
DYNAMIC MAPPING (schedule: dynamic)
─────────────────────────────────────────────────────────────
Las cajas quedan en una ZONA COMÚN:
  📦 Caja 1   📦 Caja 2   📦 Caja 3   📦 Caja 4 ...
Cada estudiante toma la siguiente caja disponible al terminar.
✓ Ideal si las cajas pesan diferente, están a distancias variables o tardan tiempos distintos.
✓ Proporciona mejor Load Balancing ante cargas desbalanceadas.
```

---

## Resumen del Caso Completo

```
1,000 LIBROS EN SALÓN ORIGEN
        │
        ▼
   [P] PARTITION: Identificar 1,000 libros como tareas independientes (1 libro = 1 tarea potencial)
        │
        ▼
   [C] COMMUNICATION: Reportes coordinados para verificar avance (Total esperado = 1,000 libros)
        │
        ▼
   [A] AGGLOMERATION: Agrupar en 20 cajas de 50 libros (De 1,000 a 20 tareas manejables)
        │
        ▼
   [M] MAPPING: Distribuir 20 cajas entre 8 estudiantes balanceadamente (~2 a 3 cajas por estudiante)
        │
        ▼
1,000 LIBROS TRASLADADOS EFICIENTEMENTE ✓
```

> *"PCAM no nos dice simplemente cómo ejecutar tareas en paralelo. Nos ayuda a decidir cómo organizar el trabajo paralelo."*

---

## Regla de Oro antes de Programar en Paralelo

| Fase | Pregunta de diseño |
| :--- | :--- |
| **P — Partition** | *What can run simultaneously?* (¿Qué puede ejecutarse en paralelo?) |
| **C — Communication** | *What information must tasks exchange?* (¿Qué información deben intercambiar?) |
| **A — Agglomeration** | *Which tasks should be grouped?* (¿Cuáles tareas deben agruparse?) |
| **M — Mapping** | *Where should each task execute?* (¿Dónde debe ejecutarse cada una?) |

> **THINK FIRST. PARALLELIZE SECOND.**

---

## Ejercicio: PCAM Challenge

### Escenario
Una universidad debe procesar las calificaciones de **20,000 estudiantes** utilizando **8 procesadores**.  
Para cada estudiante se requiere:
1. Calcular su promedio.
2. Determinar su aprobación.
3. Actualizar las estadísticas globales.
4. Calcular el promedio general de la universidad.

### Preguntas de análisis (Discusión en grupos - 3 minutos)

1. **P — Partition:**  
   ¿Cómo dividirías el problema? ¿Por estudiante (datos) o por operación/fase (funcional)?
2. **C — Communication:**  
   ¿Qué información debe compartirse entre tareas? ¿Cómo y cuándo se actualizan las estadísticas globales?
3. **A — Agglomeration:**  
   ¿Qué trabajo agruparías en bloques o chunks para reducir el overhead de scheduling y sincronización?
4. **M — Mapping:**  
   ¿Utilizarías *Static* o *Dynamic Mapping*? Justifica en función de si calcular la nota de cada estudiante toma un tiempo homogéneo o variable.