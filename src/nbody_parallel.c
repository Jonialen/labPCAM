#include "nbody.h"

#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int parse_chunk(const char *text, int *chunk) {
    size_t parsed;

    if (text == NULL || chunk == NULL) {
        return -1;
    }
    if (strcmp(text, "0") == 0) {
        *chunk = 0;
        return 0;
    }
    if (nbody_parse_positive_size(text, &parsed) != 0 || parsed > 2147483647U) {
        return -1;
    }
    *chunk = (int)parsed;
    return 0;
}

static int parse_schedule(const char *text, NBodySchedule *schedule) {
    if (strcmp(text, "static") == 0) {
        *schedule = NBODY_SCHEDULE_STATIC;
    } else if (strcmp(text, "dynamic") == 0) {
        *schedule = NBODY_SCHEDULE_DYNAMIC;
    } else if (strcmp(text, "guided") == 0) {
        *schedule = NBODY_SCHEDULE_GUIDED;
    } else {
        return -1;
    }
    return 0;
}

static const char *schedule_name(NBodySchedule schedule) {
    switch (schedule) {
        case NBODY_SCHEDULE_STATIC: return "static";
        case NBODY_SCHEDULE_DYNAMIC: return "dynamic";
        case NBODY_SCHEDULE_GUIDED: return "guided";
    }
    return "unknown";
}

int main(int argc, char **argv) {
    size_t count;
    size_t steps;
    size_t requested_threads_value;
    int chunk_size = 0;
    int actual_threads = 0;
    NBodySchedule schedule;

    if ((argc != 5 && argc != 6) ||
        nbody_parse_positive_size(argv[1], &count) != 0 ||
        nbody_parse_positive_size(argv[2], &steps) != 0 ||
        nbody_parse_positive_size(argv[3], &requested_threads_value) != 0 ||
        requested_threads_value > 2147483647U ||
        parse_schedule(argv[4], &schedule) != 0 ||
        (argc == 6 && parse_chunk(argv[5], &chunk_size) != 0)) {
        fprintf(stderr, "Usage: %s <bodies> <steps> <threads> <static|dynamic|guided> [chunk]\n",
                argv[0]);
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
    const int simulation_result = nbody_simulate_parallel(
        bodies, count, steps, (int)requested_threads_value, schedule,
        chunk_size, &actual_threads);
    const double elapsed = omp_get_wtime() - start;
    if (simulation_result != 0) {
        fprintf(stderr, "Error: parallel simulation failed.\n");
        free(bodies);
        return EXIT_FAILURE;
    }

    printf("Students: David Dominguez (23712), Jonathan Diaz (23873), Luis Padilla (23663)\n");
    printf("Mode: parallel-direct\n");
    printf("N: %zu | Steps: %zu | Seed: %llu\n", count, steps,
           (unsigned long long)NBODY_SEED);
    printf("Threads requested: %zu | Threads used: %d\n",
           requested_threads_value, actual_threads);
    printf("Schedule: %s | Chunk: %s", schedule_name(schedule),
           chunk_size == 0 ? "default" : "");
    if (chunk_size != 0) {
        printf("%d", chunk_size);
    }
    putchar('\n');
    printf("Elapsed: %.9f s\n", elapsed);
    printf("Checksum: %.12f\n", nbody_checksum(bodies, count));
    printf("Processors reported by OpenMP: %d\n", omp_get_num_procs());
    printf("Maximum threads reported by OpenMP: %d\n", omp_get_max_threads());
    free(bodies);
    return EXIT_SUCCESS;
}
