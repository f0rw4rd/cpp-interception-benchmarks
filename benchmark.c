#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdint.h>

__attribute__((noinline))
int compute_sum(int a, int b) {
    return a + b;
}

__attribute__((noinline))
uint64_t factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

__attribute__((noinline))
void process_array(int* arr, size_t size, int* result) {
    *result = 0;
    for (size_t i = 0; i < size; i++) {
        *result += arr[i];
    }
}

__attribute__((noinline))
void* allocate_and_free(size_t size) {
    void* ptr = malloc(size);
    if (ptr) {
        memset(ptr, 0x42, size);
        free(ptr);
    }
    return NULL;
}

__attribute__((noinline))
const char* test_intercept() {
    return "ORIGINAL";
}

int main() {
    const int HOT_ITERATIONS = 10000000;
    struct timespec start, end;
    
    printf("Starting benchmark...\n");
    printf("Test intercept: %s\n", test_intercept());
    
    clock_gettime(CLOCK_MONOTONIC, &start);
    volatile int sum = 0;
    for (int i = 0; i < HOT_ITERATIONS; i++) {
        sum = compute_sum(i, i + 1);
    }
    clock_gettime(CLOCK_MONOTONIC, &end);
    long ms = (end.tv_sec - start.tv_sec) * 1000 + (end.tv_nsec - start.tv_nsec) / 1000000;
    printf("Hot path: %ld ms\n", ms);
    
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (int i = 0; i < 100000; i++) {
        volatile uint64_t f = factorial(20);
    }
    clock_gettime(CLOCK_MONOTONIC, &end);
    ms = (end.tv_sec - start.tv_sec) * 1000 + (end.tv_nsec - start.tv_nsec) / 1000000;
    printf("Recursive: %ld ms\n", ms);
    
    int arr[1000];
    int result;
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (int i = 0; i < 10000; i++) {
        process_array(arr, 1000, &result);
    }
    clock_gettime(CLOCK_MONOTONIC, &end);
    ms = (end.tv_sec - start.tv_sec) * 1000 + (end.tv_nsec - start.tv_nsec) / 1000000;
    printf("Array ops: %ld ms\n", ms);
    
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (int i = 0; i < 100000; i++) {
        allocate_and_free(1024);
    }
    clock_gettime(CLOCK_MONOTONIC, &end);
    ms = (end.tv_sec - start.tv_sec) * 1000 + (end.tv_nsec - start.tv_nsec) / 1000000;
    printf("Memory ops: %ld ms\n", ms);
    
    return 0;
}