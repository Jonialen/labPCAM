#include "nbody.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

static void test_initialization_is_reproducible(void) {
    Body first[8];
    Body second[8];
    Body different[8];

    nbody_initialize(first, 8, NBODY_SEED);
    nbody_initialize(second, 8, NBODY_SEED);
    nbody_initialize(different, 8, NBODY_SEED + 1U);

    assert(memcmp(first, second, sizeof(first)) == 0);
    assert(memcmp(first, different, sizeof(first)) != 0);
    for (size_t i = 0; i < 8; ++i) {
        assert(first[i].mass >= NBODY_MIN_MASS);
        assert(first[i].mass <= NBODY_MAX_MASS);
    }
}

static void test_single_body_has_no_self_force(void) {
    Body body = {2.0, -3.0, 0.5, -0.25, 1.25};
    Body result;

    nbody_step(&body, &result, 1);

    assert(fabs(result.vx - body.vx) < 1e-14);
    assert(fabs(result.vy - body.vy) < 1e-14);
    assert(fabs(result.x - (body.x + body.vx * NBODY_DT)) < 1e-14);
    assert(fabs(result.y - (body.y + body.vy * NBODY_DT)) < 1e-14);
    assert(result.mass == body.mass);
}

static void test_two_body_accelerations_are_opposite_and_finite(void) {
    Body bodies[2] = {
        {-1.0, 0.0, 0.0, 0.0, 2.0},
        {1.0, 0.0, 0.0, 0.0, 1.0},
    };
    Body next[2];

    nbody_step(bodies, next, 2);

    assert(isfinite(next[0].vx) && isfinite(next[1].vx));
    assert(next[0].vx > 0.0);
    assert(next[1].vx < 0.0);
    assert(fabs(bodies[0].mass * next[0].vx +
                bodies[1].mass * next[1].vx) < 1e-12);
    assert(next[0].mass == bodies[0].mass);
    assert(next[1].mass == bodies[1].mass);
}

static void test_simulation_and_checksum_are_reproducible(void) {
    Body first[32];
    Body second[32];

    nbody_initialize(first, 32, NBODY_SEED);
    nbody_initialize(second, 32, NBODY_SEED);
    assert(nbody_simulate(first, 32, 4) == 0);
    assert(nbody_simulate(second, 32, 4) == 0);
    assert(memcmp(first, second, sizeof(first)) == 0);
    assert(nbody_checksum(first, 32) == nbody_checksum(second, 32));
    assert(isfinite(nbody_checksum(first, 32)));
}

static void test_positive_size_parser(void) {
    size_t value = 0;

    assert(nbody_parse_positive_size("17", &value) == 0 && value == 17);
    assert(nbody_parse_positive_size("0", &value) != 0);
    assert(nbody_parse_positive_size("-2", &value) != 0);
    assert(nbody_parse_positive_size("12x", &value) != 0);
    assert(nbody_parse_positive_size("", &value) != 0);
    assert(nbody_parse_positive_size("999999999999999999999999999999", &value) != 0);
}

static void assert_bodies_close(const Body *expected, const Body *actual,
                                size_t count, double tolerance) {
    for (size_t i = 0; i < count; ++i) {
        assert(fabs(expected[i].x - actual[i].x) <= tolerance);
        assert(fabs(expected[i].y - actual[i].y) <= tolerance);
        assert(fabs(expected[i].vx - actual[i].vx) <= tolerance);
        assert(fabs(expected[i].vy - actual[i].vy) <= tolerance);
        assert(fabs(expected[i].mass - actual[i].mass) <= tolerance);
    }
}

static void test_parallel_simulation_matches_sequential_for_schedules(void) {
    const struct {
        NBodySchedule schedule;
        int chunk;
        int threads;
    } configurations[] = {
        {NBODY_SCHEDULE_STATIC, 0, 1},
        {NBODY_SCHEDULE_STATIC, 1, 2},
        {NBODY_SCHEDULE_STATIC, 7, 4},
        {NBODY_SCHEDULE_DYNAMIC, 1, 2},
        {NBODY_SCHEDULE_DYNAMIC, 5, 4},
        {NBODY_SCHEDULE_GUIDED, 0, 2},
        {NBODY_SCHEDULE_GUIDED, 3, 4},
    };
    Body expected[64];

    nbody_initialize(expected, 64, NBODY_SEED);
    assert(nbody_simulate(expected, 64, 6) == 0);
    for (size_t test = 0; test < sizeof(configurations) / sizeof(configurations[0]); ++test) {
        Body actual[64];
        int actual_threads = 0;
        nbody_initialize(actual, 64, NBODY_SEED);
        assert(nbody_simulate_parallel(actual, 64, 6, configurations[test].threads,
                                       configurations[test].schedule,
                                       configurations[test].chunk,
                                       &actual_threads) == 0);
        assert(actual_threads >= 1 && actual_threads <= configurations[test].threads);
        assert_bodies_close(expected, actual, 64, 1e-12);
    }
}

static void test_parallel_simulation_rejects_invalid_configuration(void) {
    Body body = {0.0, 0.0, 0.0, 0.0, 1.0};
    int actual_threads = 0;

    assert(nbody_simulate_parallel(&body, 1, 1, 0, NBODY_SCHEDULE_STATIC,
                                   0, &actual_threads) != 0);
    assert(nbody_simulate_parallel(&body, 1, 1, 1, (NBodySchedule)99,
                                   0, &actual_threads) != 0);
    assert(nbody_simulate_parallel(&body, 1, 1, 1, NBODY_SCHEDULE_DYNAMIC,
                                   -1, &actual_threads) != 0);
}

int main(void) {
    test_initialization_is_reproducible();
    test_single_body_has_no_self_force();
    test_two_body_accelerations_are_opposite_and_finite();
    test_simulation_and_checksum_are_reproducible();
    test_positive_size_parser();
    test_parallel_simulation_matches_sequential_for_schedules();
    test_parallel_simulation_rejects_invalid_configuration();
    puts("All N-body unit tests passed.");
    return 0;
}
