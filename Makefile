# Prefer an installed GNU compiler (Apple's system clang does not ship with
# OpenMP enabled); fall back to the platform C compiler on other systems.
CC = $(shell command -v gcc-16 2>/dev/null || command -v gcc 2>/dev/null || command -v cc)
CXX = $(shell command -v g++-16 2>/dev/null || command -v g++ 2>/dev/null || command -v c++)
CPPFLAGS ?= -Isrc
CFLAGS ?= -std=c11 -O2 -Wall -Wextra -Wpedantic
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra -Wpedantic
OPENMP_FLAGS ?= -fopenmp
LDLIBS ?= -lm

BUILD_DIR := build
TEST_BINARY := $(BUILD_DIR)/test_nbody
SEQUENTIAL_BINARY := $(BUILD_DIR)/nbody_seq
PARALLEL_BINARY := $(BUILD_DIR)/nbody_parallel
OPTIMIZED_BINARY := $(BUILD_DIR)/nbody_optimized
CPP_SEQUENTIAL_BINARY := $(BUILD_DIR)/cpp_nbody_seq
CPP_PARALLEL_BINARY := $(BUILD_DIR)/cpp_nbody_parallel
CPP_OPTIMIZED_BINARY := $(BUILD_DIR)/cpp_nbody_optimized
CPP_TEST_BINARY := $(BUILD_DIR)/cpp_test_nbody
COMPARE_BINARY := $(BUILD_DIR)/compare_full_state
CPP_COMPARE_BINARY := $(BUILD_DIR)/cpp_compare_full_state

.PHONY: all clean test canvas

all: $(SEQUENTIAL_BINARY) $(PARALLEL_BINARY) $(OPTIMIZED_BINARY) $(CPP_SEQUENTIAL_BINARY) $(CPP_PARALLEL_BINARY) $(CPP_OPTIMIZED_BINARY)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(TEST_BINARY): tests/test_nbody.c src/nbody.c src/nbody_optimized.c src/nbody.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENMP_FLAGS) tests/test_nbody.c src/nbody.c src/nbody_optimized.c -o $@ $(LDLIBS)

$(COMPARE_BINARY): tests/compare_full_state.c src/nbody.c src/nbody_optimized.c src/nbody.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENMP_FLAGS) tests/compare_full_state.c src/nbody.c src/nbody_optimized.c -o $@ $(LDLIBS)

$(SEQUENTIAL_BINARY): src/nbody_seq.c src/nbody.c src/nbody.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENMP_FLAGS) src/nbody_seq.c src/nbody.c -o $@ $(LDLIBS)

$(PARALLEL_BINARY): src/nbody_parallel.c src/nbody.c src/nbody.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENMP_FLAGS) src/nbody_parallel.c src/nbody.c -o $@ $(LDLIBS)

$(OPTIMIZED_BINARY): src/nbody_optimized_main.c src/nbody_optimized.c src/nbody.c src/nbody.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENMP_FLAGS) src/nbody_optimized_main.c src/nbody_optimized.c src/nbody.c -o $@ $(LDLIBS)

$(CPP_TEST_BINARY): tests/test_nbody.c src_cpp/nbody.cpp src_cpp/nbody_optimized.cpp src_cpp/nbody.h | $(BUILD_DIR)
	$(CXX) -Isrc_cpp $(CXXFLAGS) $(OPENMP_FLAGS) -x c++ tests/test_nbody.c src_cpp/nbody.cpp src_cpp/nbody_optimized.cpp -o $@ $(LDLIBS)

$(CPP_COMPARE_BINARY): tests/compare_full_state.c src_cpp/nbody.cpp src_cpp/nbody_optimized.cpp src_cpp/nbody.h | $(BUILD_DIR)
	$(CXX) -Isrc_cpp $(CXXFLAGS) $(OPENMP_FLAGS) -x c++ tests/compare_full_state.c src_cpp/nbody.cpp src_cpp/nbody_optimized.cpp -o $@ $(LDLIBS)

$(CPP_SEQUENTIAL_BINARY): src_cpp/nbody_seq.cpp src_cpp/nbody.cpp src_cpp/nbody.h | $(BUILD_DIR)
	$(CXX) -Isrc_cpp $(CXXFLAGS) $(OPENMP_FLAGS) src_cpp/nbody_seq.cpp src_cpp/nbody.cpp -o $@ $(LDLIBS)

$(CPP_PARALLEL_BINARY): src_cpp/nbody_parallel.cpp src_cpp/nbody.cpp src_cpp/nbody.h | $(BUILD_DIR)
	$(CXX) -Isrc_cpp $(CXXFLAGS) $(OPENMP_FLAGS) src_cpp/nbody_parallel.cpp src_cpp/nbody.cpp -o $@ $(LDLIBS)

$(CPP_OPTIMIZED_BINARY): src_cpp/nbody_optimized_main.cpp src_cpp/nbody_optimized.cpp src_cpp/nbody.cpp src_cpp/nbody.h | $(BUILD_DIR)
	$(CXX) -Isrc_cpp $(CXXFLAGS) $(OPENMP_FLAGS) src_cpp/nbody_optimized_main.cpp src_cpp/nbody_optimized.cpp src_cpp/nbody.cpp -o $@ $(LDLIBS)

canvas: src/nbody.c src/nbody.h src/nbody_seq.c src/nbody_parallel.c scripts/build_canvas_sources.py | $(BUILD_DIR)
	python3 scripts/build_canvas_sources.py
	$(CC) $(CFLAGS) $(OPENMP_FLAGS) entrega_canvas/nbody_secuencial.c -o $(BUILD_DIR)/canvas_nbody_secuencial $(LDLIBS)
	$(CC) $(CFLAGS) $(OPENMP_FLAGS) entrega_canvas/nbody_paralelo.c -o $(BUILD_DIR)/canvas_nbody_paralelo $(LDLIBS)
	sh tests/test_cli.sh $(BUILD_DIR)/canvas_nbody_secuencial
	sh tests/test_parallel_cli.sh $(BUILD_DIR)/canvas_nbody_paralelo

test: $(TEST_BINARY) $(CPP_TEST_BINARY) $(COMPARE_BINARY) $(CPP_COMPARE_BINARY) all canvas
	python3 scripts/sync_cpp.py --check
	$(TEST_BINARY)
	sh tests/test_cli.sh $(SEQUENTIAL_BINARY)
	sh tests/test_parallel_cli.sh $(PARALLEL_BINARY)
	sh tests/test_optimized_cli.sh $(OPTIMIZED_BINARY)
	$(CPP_TEST_BINARY)
	sh tests/test_cli.sh $(CPP_SEQUENTIAL_BINARY)
	sh tests/test_parallel_cli.sh $(CPP_PARALLEL_BINARY)
	sh tests/test_optimized_cli.sh $(CPP_OPTIMIZED_BINARY)

clean:
	rm -rf $(BUILD_DIR)
