#include "nbody.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

static double max_difference(const Body *baseline, const Body *candidate,
                             size_t count) {
    double maximum = 0.0;
    for (size_t i = 0; i < count; ++i) {
        const double differences[] = {
            fabs(baseline[i].x - candidate[i].x),
            fabs(baseline[i].y - candidate[i].y),
            fabs(baseline[i].vx - candidate[i].vx),
            fabs(baseline[i].vy - candidate[i].vy),
            fabs(baseline[i].mass - candidate[i].mass),
        };
        for (size_t field = 0; field < 5; ++field) {
            if (!isfinite(differences[field])) {
                return INFINITY;
            }
            if (differences[field] > maximum) {
                maximum = differences[field];
            }
        }
    }
    return maximum;
}

int main(int argc, char **argv) {
    size_t count, steps;
    if (argc != 3 || nbody_parse_positive_size(argv[1], &count) != 0 ||
        nbody_parse_positive_size(argv[2], &steps) != 0 ||
        count > SIZE_MAX / sizeof(Body)) {
        fprintf(stderr, "Usage: %s <positive-bodies> <positive-steps>\n", argv[0]);
        return EXIT_FAILURE;
    }
    Body *sequential = (Body *)malloc(count * sizeof(Body));
    Body *direct = (Body *)malloc(count * sizeof(Body));
    Body *optimized = (Body *)malloc(count * sizeof(Body));
    if (sequential == NULL || direct == NULL || optimized == NULL) {
        fputs("Unable to allocate comparison buffers.\n", stderr);
        free(sequential);
        free(direct);
        free(optimized);
        return EXIT_FAILURE;
    }
    nbody_initialize(sequential, count, NBODY_SEED);
    nbody_initialize(direct, count, NBODY_SEED);
    nbody_initialize(optimized, count, NBODY_SEED);
    int direct_threads = 0, optimized_threads = 0;
    const int okay =
        nbody_simulate(sequential, count, steps) == 0 &&
        nbody_simulate_parallel(direct, count, steps, 8,
                                NBODY_SCHEDULE_STATIC, 0, &direct_threads) == 0 &&
        nbody_simulate_optimized_parallel(optimized, count, steps, 8,
                                          NBODY_SCHEDULE_STATIC, 0,
                                          &optimized_threads) == 0;
    if (!okay) {
        fputs("A simulation failed.\n", stderr);
        free(sequential);
        free(direct);
        free(optimized);
        return EXIT_FAILURE;
    }
    const double direct_difference = max_difference(sequential, direct, count);
    const double optimized_difference = max_difference(sequential, optimized, count);
    printf("N=%zu steps=%zu seed=%llu direct_threads=%d optimized_threads=%d\n",
           count, steps, (unsigned long long)NBODY_SEED,
           direct_threads, optimized_threads);
    printf("direct_max_abs_state_difference=%.17g\n", direct_difference);
    printf("optimized_max_abs_state_difference=%.17g\n", optimized_difference);
    printf("direct_checksum_difference=%.17g\n",
           fabs(nbody_checksum(sequential, count) - nbody_checksum(direct, count)));
    printf("optimized_checksum_difference=%.17g\n",
           fabs(nbody_checksum(sequential, count) - nbody_checksum(optimized, count)));
    free(sequential);
    free(direct);
    free(optimized);
    return isfinite(direct_difference) && isfinite(optimized_difference) &&
           direct_difference < 1e-8 && optimized_difference < 1e-8
               ? EXIT_SUCCESS : EXIT_FAILURE;
}
