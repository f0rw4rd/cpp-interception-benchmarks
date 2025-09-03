#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
__attribute__((noinline))
int compute_sum(int a, int b) {
    volatile int temp = a;
    temp += b;
    return temp;
}
__attribute__((noinline))
int compute_sum_heavy(int a, int b) {
    volatile int result = 0;
    for (int i = 0; i < 100; i++) {
        result += i * i;
        result ^= (result << 1);
    }
    return a + b;
}
__attribute__((noinline))
uint64_t factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}
__attribute__((noinline))
int process_array(int* arr, size_t size, int* result) {
    *result = 0;
    for (size_t i = 0; i < size; i++) {
        *result += arr[i];
    }
    return 0;
}
__attribute__((noinline))
int allocate_and_free(size_t size) {
    volatile void* ptr = malloc(size);
    if (ptr) {
        volatile char* data = (volatile char*)ptr;
        for (size_t i = 0; i < size && i < 10; i++) {
            data[i] = 0x42;
        }
        free((void*)ptr);
        return 1;
    }
    return 0;
}
static volatile int complex_call_count = 0;
static volatile double complex_stats_sum = 0.0;
static volatile double complex_stats_min = 1e9;
static volatile double complex_stats_max = -1e9;
__attribute__((noinline))
static uint32_t simple_hash_c(int a, int b) {
    char str[32];
    snprintf(str, sizeof(str), "%x_%x", (unsigned int)a, (unsigned int)b);
    uint32_t hash = 0;
    for (int i = 0; str[i] != '\0'; i++) {
        hash = ((hash << 5) - hash) + (unsigned char)str[i];
    }
    return hash & 0x7FFFFFFF;
}
__attribute__((noinline))
static uint64_t fibonacci_c(int n) {
    if (n <= 1) return n;
    uint64_t a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        uint64_t temp = b;
        b = a + b;
        a = temp;
    }
    return b;
}
__attribute__((noinline))
static int is_prime_c(int n) {
    if (n <= 1) return 0;
    if (n <= 3) return 1;
    if (n % 2 == 0 || n % 3 == 0) return 0;
    for (int i = 5; i * i <= n; i += 6) {
        if (n % i == 0 || n % (i + 2) == 0) return 0;
    }
    return 1;
}
__attribute__((noinline))
static int matrix_operation_c(int a, int b) {
    int matrix[10][10];
    for (int i = 0; i < 10; i++) {
        for (int j = 0; j < 10; j++) {
            matrix[i][j] = (a * i + b * j) % 100;
        }
    }
    int result = 0;
    for (int i = 0; i < 10; i++) {
        for (int j = 0; j < 10; j++) {
            result += matrix[i][j] * ((i + j) % 3 == 0 ? 1 : -1);
        }
    }
    return result;
}
__attribute__((noinline))
int compute_sum_complex(int a, int b) {
    complex_call_count++;
    uint32_t hash = simple_hash_c(a, b);
    double trig_result = 0.0;
    for (int i = 0; i < 50; i++) {
        trig_result += sin(a * i * 0.01) * cos(b * i * 0.01);
    }
    double arr[30];
    for (int i = 0; i < 30; i++) {
        arr[i] = i * trig_result;
    }
    double sum = 0.0;
    for (int i = 0; i < 30; i++) {
        if ((int)floor(arr[i]) % 2 == 0) {
            sum += arr[i] * arr[i];
        }
    }
    double value = (double)(a + b);
    complex_stats_sum += value;
    if (value < complex_stats_min) complex_stats_min = value;
    if (value > complex_stats_max) complex_stats_max = value;
    int fib_index = abs(a + b) % 25;
    uint64_t fib_value = fibonacci_c(fib_index);
    int prime_check = is_prime_c(abs(a * b) % 100);
    int matrix_result = matrix_operation_c(a, b);
    int final = (int)sum;
    for (int i = 0; i < 5; i++) {
        final = (final * 7 + (int)fib_value) % 1000;
    }
    int bits = final;
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
    if (complex_call_count % 10000 == 0) {
        char buffer[256];
        snprintf(buffer, sizeof(buffer), 
            "{\"callCount\":%d,\"sum\":%.2f,\"min\":%.2f,\"max\":%.2f}", 
            complex_call_count, complex_stats_sum, complex_stats_min, complex_stats_max);
        volatile int len = (int)strlen(buffer);
        (void)len;
    }
    return (int)((hash + fib_value + matrix_result + median) % 1000) + (a + b);
}
__attribute__((noinline))
const char* test_intercept() {
    return "ORIGINAL";
}