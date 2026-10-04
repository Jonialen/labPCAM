# Prefer an installed GNU compiler (Apple's system clang does not ship with
# OpenMP enabled); fall back to the platform C compiler on other systems.
CC = $(shell command -v gcc-16 2>/dev/null || command -v gcc 2>/dev/null || command -v cc)
CPPFLAGS ?= -Isrc
CFLAGS ?= -std=c11 -O2 -Wall -Wextra -Wpedantic
OPENMP_FLAGS ?= -fopenmp
LDLIBS ?= -lm

BUILD_DIR := build
TEST_BINARY := $(BUILD_DIR)/test_nbody
SEQUENTIAL_BINARY := $(BUILD_DIR)/nbody_seq
PARALLEL_BINARY := $(BUILD_DIR)/nbody_parallel
OPTIMIZED_BINARY := $(BUILD_DIR)/nbody_optimized

.PHONY: all clean test

all: $(SEQUENTIAL_BINARY) $(PARALLEL_BINARY) $(OPTIMIZED_BINARY)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(TEST_BINARY): tests/test_nbody.c src/nbody.c src/nbody.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENMP_FLAGS) tests/test_nbody.c src/nbody.c src/nbody_optimized.c -o $@ $(LDLIBS)

$(SEQUENTIAL_BINARY): src/nbody_seq.c src/nbody.c src/nbody.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENMP_FLAGS) src/nbody_seq.c src/nbody.c -o $@ $(LDLIBS)

$(PARALLEL_BINARY): src/nbody_parallel.c src/nbody.c src/nbody.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENMP_FLAGS) src/nbody_parallel.c src/nbody.c -o $@ $(LDLIBS)

$(OPTIMIZED_BINARY): src/nbody_optimized_main.c src/nbody_optimized.c src/nbody.c src/nbody.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENMP_FLAGS) src/nbody_optimized_main.c src/nbody_optimized.c src/nbody.c -o $@ $(LDLIBS)

test: $(TEST_BINARY) $(SEQUENTIAL_BINARY) $(PARALLEL_BINARY) $(OPTIMIZED_BINARY)
	$(TEST_BINARY)
	sh tests/test_cli.sh $(SEQUENTIAL_BINARY)
	sh tests/test_parallel_cli.sh $(PARALLEL_BINARY)
	sh tests/test_optimized_cli.sh $(OPTIMIZED_BINARY)

clean:
	rm -rf $(BUILD_DIR)
