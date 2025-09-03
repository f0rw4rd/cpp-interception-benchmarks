const cm = new CModule(`
#include <gum/guminterceptor.h>
#include <string.h>
#include <stdio.h>
inline int abs(int x) {
    return x < 0 ? -x : x;
}
#define CACHE_SIZE 1024
typedef struct {
    unsigned int key;
    int value;
    int valid;
} CacheEntry;
unsigned long long fibonacci(int n) {
    if (n <= 1) return n;
    unsigned long long a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        unsigned long long temp = b;
        b = a + b;
        a = temp;
    }
    return b;
}
int is_prime(int n) {
    if (n <= 1) return 0;
    if (n <= 3) return 1;
    if (n % 2 == 0 || n % 3 == 0) return 0;
    for (int i = 5; i * i <= n; i += 6) {
        if (n % i == 0 || n % (i + 2) == 0) return 0;
    }
    return 1;
}
void hello(void) {
    printf("Hello World from CModule\\n");
  }
void perform_complex_operations(int a, int b) {
    CacheEntry cache[CACHE_SIZE];
int cache_hits = 0;
int cache_misses = 0;
int call_count = 0;
int samples[1000];
int sample_count = 0;
long long stats_sum = 0;
int stats_min = 1000000000;
int stats_max = -1000000000;
    unsigned int hash = 5381;
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
    unsigned long long fib_value = fibonacci(fib_index);
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
}
`);
var targetFunctions = ['compute_sum', 'compute_sum_heavy', 'factorial', 'process_array', 'allocate_and_free', 'test_intercept', 'compute_sum_complex'];
function hookFunctions() {
    var libfuncs = Process.findModuleByName('libfuncs.so');
    if (libfuncs) {
        var exports = libfuncs.enumerateExports();
        var hooked = 0;
        const work = new NativeFunction(cm.perform_complex_operations, 'void', ['int', 'int']);
        targetFunctions.forEach(function (funcName) {
            var funcExport = exports.find(function (e) { return e.name === funcName; });
            if (funcExport) {
                try {
                    if (funcName === 'compute_sum_complex') {
                        Interceptor.attach(funcExport.address, {
                            onEnter: function (args) {
                                this.a = args[0].toInt32();
                                this.b = args[1].toInt32();
                                work(this.a, this.b);
                            },
                            onLeave: function (retval) {
                                work(this.a, this.b);
                                retval.replace(0x42);
                            }
                        });
                    } else if (funcName === 'test_intercept') {
                        Interceptor.attach(funcExport.address, {
                            onLeave: function (retval) {
                                retval.replace(Memory.allocUtf8String('FRIDA_CMODULE_COMPLEX'));
                            }
                        });
                    } else {
                        Interceptor.attach(funcExport.address, {
                            onLeave: function (retval) {
                                retval.replace(0x42);
                            }
                        });
                    }
                    hooked++;
                    console.log('Hooked', funcName, 'at', funcExport.address);
                } catch (e) {
                    console.log('Failed to hook', funcName, ':', e);
                }
            }
        });
        console.log('CModule complex hooks installed - hooked', hooked, 'functions');
    } else {
        setTimeout(hookFunctions, 10);
    }
}
hookFunctions();