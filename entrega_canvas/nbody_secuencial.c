/* Archivo independiente generado desde src/. No editar esta copia. */
#ifndef NBODY_H
#define NBODY_H
#include <stddef.h>
#include <stdint.h>
#define NBODY_SEED UINT64_C(42)
#define NBODY_DT 0.001
#define NBODY_GRAVITATIONAL_CONSTANT 1.0
#define NBODY_SOFTENING 0.01
#define NBODY_MIN_MASS 0.5
#define NBODY_MAX_MASS 10.0
typedef struct { double x, y, vx, vy, mass; } Body;
void nbody_initialize(Body *bodies, size_t count, uint64_t seed);
void nbody_step(const Body *current, Body *next, size_t count);
int nbody_simulate(Body *bodies, size_t count, size_t steps);
double nbody_checksum(const Body *bodies, size_t count);
int nbody_parse_positive_size(const char *text, size_t *value);
#endif


#include <errno.h>
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

static uint64_t next_random(uint64_t *state) {
    uint64_t value = *state;

    /* SplitMix64 produces a deterministic stream independent of libc rand(). */
    value += UINT64_C(0x9e3779b97f4a7c15);
    *state = value;
    value = (value ^ (value >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
    value = (value ^ (value >> 27)) * UINT64_C(0x94d049bb133111eb);
    return value ^ (value >> 31);
}

static double random_unit(uint64_t *state) {
    return (double)(next_random(state) >> 11) * (1.0 / 9007199254740992.0);
}

static double random_range(uint64_t *state, double low, double high) {
    return low + (high - low) * random_unit(state);
}

static void update_body(const Body *current, Body *next, size_t index,
                        size_t count, double softening_squared) {
    double ax = 0.0;
    double ay = 0.0;

    for (size_t j = 0; j < count; ++j) {
        if (index == j) {
            continue;
        }

        const double dx = current[j].x - current[index].x;
        const double dy = current[j].y - current[index].y;
        const double distance_squared = dx * dx + dy * dy + softening_squared;
        const double inverse_distance_cubed =
            1.0 / (distance_squared * sqrt(distance_squared));
        const double scale = NBODY_GRAVITATIONAL_CONSTANT * current[j].mass *
                             inverse_distance_cubed;

        ax += scale * dx;
        ay += scale * dy;
    }

    next[index].vx = current[index].vx + ax * NBODY_DT;
    next[index].vy = current[index].vy + ay * NBODY_DT;
    next[index].x = current[index].x + next[index].vx * NBODY_DT;
    next[index].y = current[index].y + next[index].vy * NBODY_DT;
    next[index].mass = current[index].mass;
}

void nbody_initialize(Body *bodies, size_t count, uint64_t seed) {
    uint64_t state = seed;

    for (size_t i = 0; i < count; ++i) {
        bodies[i].x = random_range(&state, -100.0, 100.0);
        bodies[i].y = random_range(&state, -100.0, 100.0);
        bodies[i].vx = random_range(&state, -1.0, 1.0);
        bodies[i].vy = random_range(&state, -1.0, 1.0);
        bodies[i].mass = random_range(&state, NBODY_MIN_MASS, NBODY_MAX_MASS);
    }
}

void nbody_step(const Body *current, Body *next, size_t count) {
    const double softening_squared = NBODY_SOFTENING * NBODY_SOFTENING;

    for (size_t i = 0; i < count; ++i) {
        update_body(current, next, i, count, softening_squared);
    }
}

int nbody_simulate(Body *bodies, size_t count, size_t steps) {
    if (bodies == NULL || count == 0 || count > SIZE_MAX / sizeof(Body)) {
        return -1;
    }

    Body *next = (Body *)malloc(count * sizeof(*next));
    if (next == NULL) {
        return -1;
    }

    for (size_t step = 0; step < steps; ++step) {
        nbody_step(bodies, next, count);
        memcpy(bodies, next, count * sizeof(*bodies));
    }

    free(next);
    return 0;
}

double nbody_checksum(const Body *bodies, size_t count) {
    double checksum = 0.0;

    for (size_t i = 0; i < count; ++i) {
        checksum += bodies[i].x * 0.5 + bodies[i].y * 0.25 +
                    bodies[i].vx * 0.125 + bodies[i].vy * 0.0625 +
                    bodies[i].mass * 0.03125;
    }
    return checksum;
}

int nbody_parse_positive_size(const char *text, size_t *value) {
    char *end = NULL;
    unsigned long long parsed;

    if (text == NULL || value == NULL || text[0] == '\0' || text[0] == '-') {
        return -1;
    }
    for (const char *cursor = text; *cursor != '\0'; ++cursor) {
        if (*cursor < '0' || *cursor > '9') {
            return -1;
        }
    }

    errno = 0;
    parsed = strtoull(text, &end, 10);
    if (errno == ERANGE || end == text || *end != '\0' || parsed == 0 ||
        parsed > SIZE_MAX) {
        return -1;
    }
    *value = (size_t)parsed;
    return 0;
}


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
