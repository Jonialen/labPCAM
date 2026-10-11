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

typedef struct {
    double x;
    double y;
    double vx;
    double vy;
    double mass;
} Body;

typedef enum {
    NBODY_SCHEDULE_STATIC,
    NBODY_SCHEDULE_DYNAMIC,
    NBODY_SCHEDULE_GUIDED
} NBodySchedule;

void nbody_initialize(Body *bodies, size_t count, uint64_t seed);
void nbody_step(const Body *current, Body *next, size_t count);
int nbody_simulate(Body *bodies, size_t count, size_t steps);
int nbody_step_parallel(const Body *current, Body *next, size_t count,
                        int requested_threads, NBodySchedule schedule,
                        int chunk_size, int *actual_threads);
int nbody_simulate_parallel(Body *bodies, size_t count, size_t steps,
                            int requested_threads, NBodySchedule schedule,
                            int chunk_size, int *actual_threads);
int nbody_step_optimized_parallel(const Body *current, Body *next, size_t count,
                                  int requested_threads, NBodySchedule schedule,
                                  int chunk_size, int *actual_threads);
int nbody_simulate_optimized_parallel(Body *bodies, size_t count, size_t steps,
                                      int requested_threads, NBodySchedule schedule,
                                      int chunk_size, int *actual_threads);
double nbody_checksum(const Body *bodies, size_t count);
int nbody_parse_positive_size(const char *text, size_t *value);

#endif


#include <errno.h>
#include <math.h>
#include <omp.h>
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

static int nbody_openmp_schedule(NBodySchedule schedule, omp_sched_t *kind) {
    switch (schedule) {
        case NBODY_SCHEDULE_STATIC:
            *kind = omp_sched_static;
            return 0;
        case NBODY_SCHEDULE_DYNAMIC:
            *kind = omp_sched_dynamic;
            return 0;
        case NBODY_SCHEDULE_GUIDED:
            *kind = omp_sched_guided;
            return 0;
    }
    return -1;
}

int nbody_step_parallel(const Body *current, Body *next, size_t count,
                        int requested_threads, NBodySchedule schedule,
                        int chunk_size, int *actual_threads) {
    omp_sched_t openmp_schedule;
    int observed_threads = 0;

    if (current == NULL || next == NULL || count == 0 || requested_threads <= 0 ||
        chunk_size < 0 || nbody_openmp_schedule(schedule, &openmp_schedule) != 0) {
        return -1;
    }
    omp_set_schedule(openmp_schedule, chunk_size);

    #pragma omp parallel num_threads(requested_threads) shared(observed_threads)
    {
        #pragma omp single
        observed_threads = omp_get_num_threads();

        #pragma omp for schedule(runtime)
        for (size_t i = 0; i < count; ++i) {
            update_body(current, next, i, count,
                        NBODY_SOFTENING * NBODY_SOFTENING);
        }
    }

    if (actual_threads != NULL) {
        *actual_threads = observed_threads;
    }
    return 0;
}

int nbody_simulate_parallel(Body *bodies, size_t count, size_t steps,
                            int requested_threads, NBodySchedule schedule,
                            int chunk_size, int *actual_threads) {
    omp_sched_t openmp_schedule;
    if (bodies == NULL || count == 0 || count > SIZE_MAX / sizeof(Body) ||
        requested_threads <= 0 || chunk_size < 0 ||
        nbody_openmp_schedule(schedule, &openmp_schedule) != 0) {
        return -1;
    }

    Body *buffer = (Body *)malloc(count * sizeof(*buffer));
    if (buffer == NULL) {
        return -1;
    }

    Body *source = bodies;
    Body *destination = buffer;
    for (size_t step = 0; step < steps; ++step) {
        if (nbody_step_parallel(source, destination, count, requested_threads,
                                schedule, chunk_size, actual_threads) != 0) {
            free(buffer);
            return -1;
        }
        Body *swap = source;
        source = destination;
        destination = swap;
    }
    if (source != bodies) {
        memcpy(bodies, source, count * sizeof(*bodies));
    }

    free(buffer);
    return 0;
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
