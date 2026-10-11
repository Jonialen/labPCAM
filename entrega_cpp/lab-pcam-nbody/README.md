# Entrega C++17 · Laboratorio PCAM + OpenMP

Integrantes: David Domínguez (23712), Jonathan Diaz (23873), Luis Padilla (23663).

Compilar con `make all` usando G++ con OpenMP. Ejecutar:

```sh
./nbody_seq 5000 10
./nbody_parallel 5000 10 8 static
./nbody_optimized 5000 10 8 static
```

`results.csv` resume tres repeticiones por configuración; `results_raw.csv`
conserva las 33 mediciones C++17. `measurements/` conserva los cuatro CSV
originales, incluidos los datos C11 con los que se compara C++17.
`report.pdf` explica PCAM, comparación C/C++17,
corrección y conclusiones. `evidence/` contiene la compilación, las
ejecuciones, el hardware y la comparación numérica.
`diseno_pcam_previo.pdf` presenta el diseño PCAM con pseudocódigo anotado.

Los fuentes `.cpp` compilan con `-std=c++17`. Se mantienen sincronizados con
la referencia C11 del repositorio mediante `scripts/sync_cpp.py` y pasan la
misma suite numérica y de CLI.
