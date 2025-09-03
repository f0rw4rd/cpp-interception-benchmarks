#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
static int (*original_compute_sum)(int, int) = NULL;
static int (*original_compute_sum_heavy)(int, int) = NULL;
static int (*original_compute_sum_complex)(int, int) = NULL;
static uint64_t (*original_factorial)(int) = NULL;
static int (*original_process_array)(int*, size_t, int*) = NULL;
static int (*original_allocate_and_free)(size_t) = NULL;
static const char* (*original_test_intercept)(void) = NULL;
static volatile int counter = 0;
static void __attribute__((constructor)) init_hooks() {
    fprintf(stderr, "LD_PRELOAD: Initializing hooks...\n");
    original_compute_sum = dlsym(RTLD_NEXT, "compute_sum");
    if (!original_compute_sum) {
        fprintf(stderr, "ERROR: Failed to find compute_sum: %s\n", dlerror());
        exit(1);
    }
    original_compute_sum_heavy = dlsym(RTLD_NEXT, "compute_sum_heavy");
    if (!original_compute_sum_heavy) {
        fprintf(stderr, "ERROR: Failed to find compute_sum_heavy: %s\n", dlerror());
        exit(1);
    }
    original_compute_sum_complex = dlsym(RTLD_NEXT, "compute_sum_complex");
    if (!original_compute_sum_complex) {
        fprintf(stderr, "ERROR: Failed to find compute_sum_complex: %s\n", dlerror());
        exit(1);
    }
    original_factorial = dlsym(RTLD_NEXT, "factorial");
    if (!original_factorial) {
        fprintf(stderr, "ERROR: Failed to find factorial: %s\n", dlerror());
        exit(1);
    }
    original_process_array = dlsym(RTLD_NEXT, "process_array");
    if (!original_process_array) {
        fprintf(stderr, "ERROR: Failed to find process_array: %s\n", dlerror());
        exit(1);
    }
    original_allocate_and_free = dlsym(RTLD_NEXT, "allocate_and_free");
    if (!original_allocate_and_free) {
        fprintf(stderr, "ERROR: Failed to find allocate_and_free: %s\n", dlerror());
        exit(1);
    }
    original_test_intercept = dlsym(RTLD_NEXT, "test_intercept");
    if (!original_test_intercept) {
        fprintf(stderr, "ERROR: Failed to find test_intercept: %s\n", dlerror());
        exit(1);
    }
    fprintf(stderr, "LD_PRELOAD: All hooks initialized successfully\n");
}
int compute_sum(int a, int b) {
    counter++;
    original_compute_sum(a, b);
    return 0x42;
}
int compute_sum_heavy(int a, int b) {
    counter++;
    original_compute_sum_heavy(a, b);
    return 0x42;
}
static int is_prime(int n) {
    if (n <= 1) return 0;
    if (n <= 3) return 1;
    if (n % 2 == 0 || n % 3 == 0) return 0;
    for (int i = 5; i * i <= n; i += 6) {
        if (n % i == 0 || n % (i + 2) == 0) return 0;
    }
    return 1;
}
static uint64_t fibonacci(int n) {
    if (n <= 1) return n;
    uint64_t a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        uint64_t temp = b;
        b = a + b;
        a = temp;
    }
    return b;
}
#define CACHE_SIZE 1024
static struct {
    uint32_t key;
    int value;
    int valid;
} cache[CACHE_SIZE];
static int cache_hits = 0;
static int cache_misses = 0;
int compute_sum_complex(int a, int b) {
    counter++;
    uint32_t hash = 5381;
    int values[2] = {a, b};
    for (int i = 0; i < 2; i++) {
        hash = ((hash << 5) + hash) + values[i];
    }
    int cache_idx = hash % CACHE_SIZE;
    int cached_result = 0;
    if (cache[cache_idx].valid && cache[cache_idx].key == hash) {
        cached_result = cache[cache_idx].value;
        cache_hits++;
    } else {
        cache_misses++;
        long long complex_result = 0;
        for (int i = 0; i < 50; i++) {
            int val_a = (a * i * i) % 1000000;
            int val_b = (b * i * i * i) % 1000000;
            complex_result += (val_a * val_b) / 1000;
            complex_result ^= (val_a << 3) | (val_b >> 2);
        }
        int arr[30];
        for (int i = 0; i < 30; i++) {
            arr[i] = i * (complex_result % 1000);
        }
        int filtered[30];
        int filtered_count = 0;
        for (int i = 0; i < 30; i++) {
            if (arr[i] % 2 == 0) {
                filtered[filtered_count++] = arr[i] * arr[i];
            }
        }
        int sum = 0;
        for (int i = 0; i < filtered_count; i++) {
            sum += filtered[i];
        }
        cached_result = sum;
        cache[cache_idx].key = hash;
        cache[cache_idx].value = cached_result;
        cache[cache_idx].valid = 1;
    }
    static int samples[1000];
    static int sample_count = 0;
    static long long stats_sum = 0;
    static int stats_min = 1000000000, stats_max = -1000000000;
    int value = a + b;
    samples[sample_count % 1000] = value;
    sample_count++;
    stats_sum += value;
    if (value < stats_min) stats_min = value;
    if (value > stats_max) stats_max = value;
    int mean = stats_sum / (sample_count > 0 ? sample_count : 1);
    long long variance = 0;
    int samples_to_check = sample_count < 1000 ? sample_count : 1000;
    for (int i = 0; i < samples_to_check; i++) {
        int diff = samples[i] - mean;
        variance += diff * diff;
    }
    variance /= samples_to_check > 0 ? samples_to_check : 1;
    int fib_index = abs(a + b) % 25;
    uint64_t fib_value = fibonacci(fib_index);
    int prime_check = is_prime(abs(a * b) % 100);
    int matrix[10][10];
    for (int i = 0; i < 10; i++) {
        for (int j = 0; j < 10; j++) {
            matrix[i][j] = (a * i + b * j) % 100;
        }
    }
    int matrix_result = 0;
    for (int i = 0; i < 10; i++) {
        for (int j = 0; j < 10; j++) {
            matrix_result += matrix[i][j] * ((i + j) % 3 == 0 ? 1 : -1);
        }
    }
    int bits = (int)cached_result;
    bits = ((bits & 0xFF) << 8) | ((bits >> 8) & 0xFF);
    bits ^= matrix_result;
    int temp_array[20];
    for (int i = 0; i < 20; i++) {
        temp_array[i] = (bits + i) * (prime_check ? 2 : 1);
    }
    for (int i = 0; i < 19; i++) {
        for (int j = 0; j < 19 - i; j++) {
            if (temp_array[j] > temp_array[j + 1]) {
                int temp = temp_array[j];
                temp_array[j] = temp_array[j + 1];
                temp_array[j + 1] = temp;
            }
        }
    }
    int median = temp_array[10];
    if (counter % 10000 == 0) {
        char buffer[256];
        snprintf(buffer, sizeof(buffer), "{\"cache_hits\":%d,\"cache_misses\":%d,\"sample_count\":%d}",
                 cache_hits, cache_misses, sample_count);
        volatile int len = strlen(buffer);
        (void)len;
    }
    original_compute_sum_complex(a, b);
    return 0x42;
}
uint64_t factorial(int n) {
    counter++;
    original_factorial(n);
    return 0x42;
}
int process_array(int* arr, size_t size, int* result) {
    counter++;
    original_process_array(arr, size, result);
    return 0x42;
}
int allocate_and_free(size_t size) {
    counter++;
    original_allocate_and_free(size);
    return 0x42;
}
const char* test_intercept() {
    counter++;
    return "LD_PRELOAD_HOOKED";
}