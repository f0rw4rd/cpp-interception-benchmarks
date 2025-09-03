#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdint.h>
#include <inttypes.h>
#include <sys/resource.h>
#include "libfuncs.h"
void validate_interception();
static int is_intercepted = 0;
void check_intercept_failure(const char* func_name, int32_t result, uint32_t call_count) {
    if (is_intercepted && result != 0x42) {
        fprintf(stderr, "INTERCEPT FAILURE: %s returned %d (expected 0x42) at call #%u\n", 
                func_name, result, call_count);
        exit(1);
    }
}
void check_intercept_failure_u64(const char* func_name, uint64_t result, uint32_t call_count) {
    if (is_intercepted && result != 0x42) {
        fprintf(stderr, "INTERCEPT FAILURE: %s returned %" PRIu64 " (expected 0x42) at call #%u\n", 
                func_name, result, call_count);
        exit(1);
    }
}
int64_t get_memory_usage() {
    struct rusage usage;
    getrusage(RUSAGE_SELF, &usage);
    return (int64_t)usage.ru_maxrss;
}
void validate_interception() {
    const char* intercept_status = test_intercept();  
    printf("Test intercept: %s\n", intercept_status);
    const char* skip_validation = getenv("SKIP_INTERCEPT_VALIDATION");
    if (skip_validation && strcmp(skip_validation, "1") == 0) {
        return;
    }
    int32_t test_compute = compute_sum(5, 5);
    int32_t test_heavy = compute_sum_heavy(3, 4);
    uint64_t test_fact = factorial(5);
    int32_t test_result;
    int32_t test_array[5] = {1, 2, 3, 4, 5};
    process_array(test_array, 5, &test_result);
    int32_t test_alloc = allocate_and_free(100);
    if (test_compute != 0x42) {
        fprintf(stderr, "ERROR: compute_sum not overriding return value! Got %d, expected 0x42\n", test_compute);
        exit(1);
    }
    if (test_heavy != 0x42) {
        fprintf(stderr, "ERROR: compute_sum_heavy not overriding return value! Got %d, expected 0x42\n", test_heavy);
        exit(1);
    }
    if (test_fact != 0x42) {
        fprintf(stderr, "ERROR: factorial not overriding return value! Got %" PRIu64 ", expected 0x42\n", test_fact);
        exit(1);
    }
    if (test_alloc != 0x42) {
        fprintf(stderr, "ERROR: allocate_and_free not overriding return value! Got %d, expected 0x42\n", test_alloc);
        exit(1);
    }
    printf("All return value overrides working (all functions return 0x42)\n");
    is_intercepted = 1;
}
int main() {
    const uint32_t HOT_ITERATIONS = 1000000U; 
    struct timespec start, end;
    printf("Starting benchmark...\n");
    validate_interception();
    clock_gettime(CLOCK_MONOTONIC, &start);
    volatile int32_t sum = 0;
    for (uint32_t i = 0; i < HOT_ITERATIONS; i++) {
        sum = compute_sum((int32_t)i, (int32_t)i + 1);
        if (i % 100000U == 0) {
            check_intercept_failure("compute_sum", sum, i);
        }
    }
    check_intercept_failure("compute_sum", sum, HOT_ITERATIONS);
    clock_gettime(CLOCK_MONOTONIC, &end);
    int64_t us = (end.tv_sec - start.tv_sec) * 1000000LL + (end.tv_nsec - start.tv_nsec) / 1000LL;
    printf("Hot path: %" PRId64 " us\n", us);
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (uint32_t i = 0; i < HOT_ITERATIONS; i++) {
        sum = compute_sum_heavy((int32_t)i, (int32_t)i + 1);
        if (i % 100000U == 0) {
            check_intercept_failure("compute_sum_heavy", sum, i);
        }
    }
    check_intercept_failure("compute_sum_heavy", sum, HOT_ITERATIONS);
    clock_gettime(CLOCK_MONOTONIC, &end);
    us = (end.tv_sec - start.tv_sec) * 1000000LL + (end.tv_nsec - start.tv_nsec) / 1000LL;
    printf("Heavy work: %" PRId64 " us\n", us);
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (uint32_t i = 0; i < HOT_ITERATIONS; i++) {
        volatile uint64_t f = factorial(20);
        if (i % 100000U == 0) {
            check_intercept_failure_u64("factorial", f, i);
        }
        (void)f;
    }
    clock_gettime(CLOCK_MONOTONIC, &end);
    us = (end.tv_sec - start.tv_sec) * 1000000LL + (end.tv_nsec - start.tv_nsec) / 1000LL;
    printf("Recursive: %" PRId64 " us\n", us);
    int32_t arr[1000];
    int32_t result;
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (uint32_t i = 0; i < HOT_ITERATIONS / 10U; i++) {
        int32_t array_result = process_array(arr, 1000, &result);
        if (i % 10000U == 0) {
            check_intercept_failure("process_array", array_result, i);
        }
    }
    clock_gettime(CLOCK_MONOTONIC, &end);
    us = (end.tv_sec - start.tv_sec) * 1000000LL + (end.tv_nsec - start.tv_nsec) / 1000LL;
    printf("Array ops: %" PRId64 " us\n", us);
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (uint32_t i = 0; i < HOT_ITERATIONS; i++) {
        int32_t alloc_result = allocate_and_free(1024);
        if (i % 100000U == 0) {
            check_intercept_failure("allocate_and_free", alloc_result, i);
        }
    }
    clock_gettime(CLOCK_MONOTONIC, &end);
    us = (end.tv_sec - start.tv_sec) * 1000000LL + (end.tv_nsec - start.tv_nsec) / 1000LL;
    printf("Memory ops: %" PRId64 " us\n", us);
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (uint32_t i = 0; i < HOT_ITERATIONS; i++) {
        int32_t complex_result = compute_sum_complex((int32_t)(i % 100), (int32_t)((i + 1) % 100));
        if (i % 100000U == 0) {
            check_intercept_failure("compute_sum_complex", complex_result, i);
        }
    }
    clock_gettime(CLOCK_MONOTONIC, &end);
    us = (end.tv_sec - start.tv_sec) * 1000000LL + (end.tv_nsec - start.tv_nsec) / 1000LL;
    printf("Complex ops: %" PRId64 " us\n", us);
    int64_t memory_kb = get_memory_usage();
    printf("Max memory: %" PRId64 " KB\n", memory_kb);
    (void)sum;
    return 0;
}