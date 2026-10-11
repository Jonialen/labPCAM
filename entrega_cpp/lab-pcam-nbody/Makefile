CXX := $(shell command -v g++-16 2>/dev/null || command -v g++ 2>/dev/null || command -v c++)
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra -Wpedantic -fopenmp
LDLIBS ?= -lm

.PHONY: all clean
all: nbody_seq nbody_parallel nbody_optimized

nbody_seq: src/nbody_seq.cpp src/nbody.cpp src/nbody.h
	$(CXX) $(CXXFLAGS) src/nbody_seq.cpp src/nbody.cpp -o $@ $(LDLIBS)

nbody_parallel: src/nbody_parallel.cpp src/nbody.cpp src/nbody.h
	$(CXX) $(CXXFLAGS) src/nbody_parallel.cpp src/nbody.cpp -o $@ $(LDLIBS)

nbody_optimized: src/nbody_optimized_main.cpp src/nbody_optimized.cpp src/nbody.cpp src/nbody.h
	$(CXX) $(CXXFLAGS) src/nbody_optimized_main.cpp src/nbody_optimized.cpp src/nbody.cpp -o $@ $(LDLIBS)

clean:
	rm -f nbody_seq nbody_parallel nbody_optimized
