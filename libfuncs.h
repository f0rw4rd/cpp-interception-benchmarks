#ifndef LIBFUNCS_H
#define LIBFUNCS_H
#include <stdint.h>
#include <stddef.h>
int compute_sum(int a, int b);
int compute_sum_heavy(int a, int b);
int compute_sum_complex(int a, int b);
uint64_t factorial(int n);
int process_array(int* arr, size_t size, int* result);
int allocate_and_free(size_t size);
const char* test_intercept();
#endif