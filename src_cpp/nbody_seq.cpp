#include "nbody.h"

#include <omp.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    size_t count;
    size_t steps;

    if (argc != 3 || nbody_parse_positive_size(argv[1], &count) != 0 ||
        nbody_parse_positive_size(argv[2], &steps) != 0) {
        fprintf(stderr, "Usage: %s <positive-body-count> <positive-step-count>\n", argv[0]);
        return EXIT_FAILURE;
    }
    if (count > SIZE_MAX / sizeof(Body)) {
        fprintf(stderr, "Error: body count is too large.\n");
        return EXIT_FAILURE;
    }

    Body *bodies = (Body *)malloc(count * sizeof(*bodies));
    if (bodies == NULL) {
        fprintf(stderr, "Error: unable to allocate memory for %zu bodies.\n", count);
        return EXIT_FAILURE;
    }

    nbody_initialize(bodies, count, NBODY_SEED);
    const double start = omp_get_wtime();
    const int simulation_result = nbody_simulate(bodies, count, steps);
    const double elapsed = omp_get_wtime() - start;
    if (simulation_result != 0) {
        fprintf(stderr, "Error: simulation failed.\n");
        free(bodies);
        return EXIT_FAILURE;
    }

    printf("Students: David Dominguez (23712), Jonathan Diaz (23873), Luis Padilla (23663)\n");
    printf("Mode: sequential\n");
    printf("N: %zu | Steps: %zu | Seed: %llu\n", count, steps,
           (unsigned long long)NBODY_SEED);
    printf("Elapsed: %.9f s\n", elapsed);
    printf("Checksum: %.12f\n", nbody_checksum(bodies, count));
    printf("Processors reported by OpenMP: %d\n", omp_get_num_procs());
    printf("Maximum threads reported by OpenMP: %d\n", omp_get_max_threads());
    free(bodies);
    return EXIT_SUCCESS;
}
