#include "nbody.h"

#include <omp.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

static int schedule_kind(NBodySchedule schedule, omp_sched_t *kind) {
    switch (schedule) {
        case NBODY_SCHEDULE_STATIC: *kind = omp_sched_static; return 0;
        case NBODY_SCHEDULE_DYNAMIC: *kind = omp_sched_dynamic; return 0;
        case NBODY_SCHEDULE_GUIDED: *kind = omp_sched_guided; return 0;
    }
    return -1;
}

int nbody_step_optimized_parallel(const Body *current, Body *next, size_t count,
                                  int requested_threads, NBodySchedule schedule,
                                  int chunk_size, int *actual_threads) {
    omp_sched_t kind;
    if (current == NULL || next == NULL || count == 0 || requested_threads <= 0 ||
        chunk_size < 0 || schedule_kind(schedule, &kind) != 0 ||
        count > SIZE_MAX / (size_t)requested_threads / (2 * sizeof(double))) {
        return -1;
    }

    /* Private planes cost O(requested_threads * bodies) memory and a matching
     * reduction pass; this trades bounded storage/reduction work for avoiding
     * contended atomics on every pair endpoint. */
    const size_t elements = count * (size_t)requested_threads * 2;
    double *partial = (double *)calloc(elements, sizeof(*partial));
    if (partial == NULL) {
        return -1;
    }

    int observed_threads = 0;
    omp_set_schedule(kind, chunk_size);
    #pragma omp parallel num_threads(requested_threads) shared(observed_threads, partial)
    {
        const int thread_id = omp_get_thread_num();
        double *partial_x = partial + (size_t)thread_id * count * 2;
        double *partial_y = partial_x + count;

        #pragma omp single
        observed_threads = omp_get_num_threads();

        /* Each unordered pair (i,j), i<j, is evaluated exactly once. The
         * thread-local acceleration planes avoid atomics on both endpoints. */
        #pragma omp for schedule(runtime)
        for (size_t i = 0; i < count; ++i) {
            for (size_t j = i + 1; j < count; ++j) {
                const double dx = current[j].x - current[i].x;
                const double dy = current[j].y - current[i].y;
                const double distance_squared = dx * dx + dy * dy +
                    NBODY_SOFTENING * NBODY_SOFTENING;
                const double inverse_distance_cubed =
                    1.0 / (distance_squared * sqrt(distance_squared));
                const double scale = NBODY_GRAVITATIONAL_CONSTANT *
                    inverse_distance_cubed;

                partial_x[i] += scale * current[j].mass * dx;
                partial_y[i] += scale * current[j].mass * dy;
                partial_x[j] -= scale * current[i].mass * dx;
                partial_y[j] -= scale * current[i].mass * dy;
            }
        }

        /* The worksharing barrier above completes all private accumulators.
         * Each output body is then owned by one thread while reducing them. */
        #pragma omp for schedule(runtime)
        for (size_t i = 0; i < count; ++i) {
            double ax = 0.0;
            double ay = 0.0;
            for (int thread = 0; thread < observed_threads; ++thread) {
                const double *thread_x = partial + (size_t)thread * count * 2;
                const double *thread_y = thread_x + count;
                ax += thread_x[i];
                ay += thread_y[i];
            }
            next[i].vx = current[i].vx + ax * NBODY_DT;
            next[i].vy = current[i].vy + ay * NBODY_DT;
            next[i].x = current[i].x + next[i].vx * NBODY_DT;
            next[i].y = current[i].y + next[i].vy * NBODY_DT;
            next[i].mass = current[i].mass;
        }
    }

    if (actual_threads != NULL) {
        *actual_threads = observed_threads;
    }
    free(partial);
    return 0;
}

int nbody_simulate_optimized_parallel(Body *bodies, size_t count, size_t steps,
                                      int requested_threads, NBodySchedule schedule,
                                      int chunk_size, int *actual_threads) {
    omp_sched_t unused;
    if (bodies == NULL || count == 0 || count > SIZE_MAX / sizeof(Body) ||
        requested_threads <= 0 || chunk_size < 0 ||
        schedule_kind(schedule, &unused) != 0) {
        return -1;
    }
    if (actual_threads != NULL) {
        *actual_threads = 0;
    }

    Body *buffer = (Body *)malloc(count * sizeof(*buffer));
    if (buffer == NULL) {
        return -1;
    }
    Body *source = bodies;
    Body *destination = buffer;
    int observed_threads = 0;
    for (size_t step = 0; step < steps; ++step) {
        if (nbody_step_optimized_parallel(source, destination, count,
                                          requested_threads, schedule, chunk_size,
                                          &observed_threads) != 0) {
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
    if (actual_threads != NULL) {
        *actual_threads = observed_threads;
    }
    free(buffer);
    return 0;
}
