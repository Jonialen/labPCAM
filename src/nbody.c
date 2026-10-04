#include "nbody.h"

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
    if (bodies == NULL || count == 0 || count > SIZE_MAX / sizeof(Body) ||
        requested_threads <= 0 || chunk_size < 0 ||
        nbody_openmp_schedule(schedule, &(omp_sched_t){0}) != 0) {
        return -1;
    }

    Body *buffer = malloc(count * sizeof(*buffer));
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

    Body *next = malloc(count * sizeof(*next));
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
