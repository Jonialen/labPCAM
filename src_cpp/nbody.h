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
