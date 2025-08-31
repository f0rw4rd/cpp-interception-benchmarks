#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

static int sum_count = 0;
static int factorial_count = 0;
static int array_count = 0;
static int alloc_count = 0;

static volatile int heavy_calculation() {
    volatile int result = 0;
    for (int i = 0; i < 1000000; i++) {
        result += i * i;
        result ^= (result << 1);
    }
    return result;
}

__attribute__((noinline))
int compute_sum(int a, int b) {
    sum_count++;
    heavy_calculation();
    return a + b;
}

__attribute__((noinline))
uint64_t factorial(int n) {
    factorial_count++;
    heavy_calculation();
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

__attribute__((noinline))
void process_array(int* arr, size_t size, int* result) {
    array_count++;
    heavy_calculation();
    *result = 0;
    for (size_t i = 0; i < size; i++) {
        *result += arr[i];
    }
}

__attribute__((noinline))
void* allocate_and_free(size_t size) {
    alloc_count++;
    heavy_calculation();
    void* ptr = malloc(size);
    if (ptr) {
        memset(ptr, 0x42, size);
        free(ptr);
    }
    return NULL;
}

__attribute__((noinline))
const char* test_intercept() {
    heavy_calculation();
    return "LD_PRELOAD_HOOKED";
}