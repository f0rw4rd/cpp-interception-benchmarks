#include <stdio.h>
#include <stdlib.h>

int compute_sum(int a, int b);
void* allocate_and_free(size_t size);

int main() {
    printf("Testing LD_PRELOAD hooks...\n");
    
    int result = compute_sum(5, 10);
    printf("compute_sum(5, 10) = %d\n", result);
    
    void* ptr = allocate_and_free(1024);
    printf("allocate_and_free(1024) = %p\n", ptr);
    
    if (ptr == NULL) {
        printf("WARNING: allocate_and_free returned NULL (not doing real work!)\n");
    } else {
        printf("allocate_and_free returned valid pointer\n");
    }
    
    return 0;
}