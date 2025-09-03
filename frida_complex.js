var targetFunctions = ['compute_sum', 'compute_sum_heavy', 'factorial', 'process_array', 'allocate_and_free', 'test_intercept', 'compute_sum_complex'];
var TRIG_ITERATIONS = 50;
var ARRAY_SIZE = 30;
var MATRIX_SIZE = 10;
var MAX_CACHE_SIZE = 5000;
var FIB_MAX = 25;
var cache = {};
var callCount = 0;
var samples = [];
var stats = { min: Infinity, max: -Infinity, sum: 0, count: 0 };
function simpleHash(str) {
    var hash = 0;
    for (var i = 0; i < str.length; i++) {
        var char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    return Math.abs(hash).toString(16).substring(0, 8);
}
function analyzeValue(value) {
    samples.push(value);
    if (samples.length > 1000) {
        samples.shift();
    }
    stats.sum += value;
    stats.count++;
    stats.min = Math.min(stats.min, value);
    stats.max = Math.max(stats.max, value);
    var mean = stats.sum / stats.count;
    var variance = 0;
    for (var i = 0; i < samples.length; i++) {
        variance += Math.pow(samples[i] - mean, 2);
    }
    variance = variance / samples.length;
    return {
        mean: mean,
        variance: variance,
        stdDev: Math.sqrt(variance)
    };
}
var fibCache = {};
function fibonacci(n) {
    if (n <= 1) return n;
    if (fibCache[n]) return fibCache[n];
    var a = 0, b = 1;
    for (var i = 2; i <= n; i++) {
        var temp = b;
        b = a + b;
        a = temp;
    }
    fibCache[n] = b;
    return b;
}
function processString(a, b) {
    var key = a.toString(16) + '_' + b.toString(16);
    var reversed = key.split('').reverse().join('');
    var upper = reversed.toUpperCase();
    var pattern = /[A-F]/g;
    var replaced = upper.replace(pattern, 'X');
    return replaced;
}
function isPrime(n) {
    if (n <= 1) return false;
    if (n <= 3) return true;
    if (n % 2 === 0 || n % 3 === 0) return false;
    for (var i = 5; i * i <= n; i += 6) {
        if (n % i === 0 || n % (i + 2) === 0) return false;
    }
    return true;
}
function matrixOperation(a, b) {
    var matrix = [];
    for (var i = 0; i < MATRIX_SIZE; i++) {
        matrix[i] = [];
        for (var j = 0; j < MATRIX_SIZE; j++) {
            matrix[i][j] = (a * i + b * j) % 100;
        }
    }
    var result = 0;
    for (var i = 0; i < MATRIX_SIZE; i++) {
        for (var j = 0; j < MATRIX_SIZE; j++) {
            result += matrix[i][j] * ((i + j) % 3 === 0 ? 1 : -1);
        }
    }
    return result;
}
function complexThing(a, b) {
    var processed = processString(a, b);
    var cacheKey = simpleHash(processed);
    if (!cache[cacheKey]) {
        var result = 0;
        for (var i = 0; i < TRIG_ITERATIONS; i++) {
            result += Math.sin(a * i * 0.01) * Math.cos(b * i * 0.01);
        }
        var arr = [];
        for (var i = 0; i < ARRAY_SIZE; i++) {
            arr.push(i * result);
        }
        var filtered = [];
        for (var i = 0; i < arr.length; i++) {
            if (Math.floor(arr[i]) % 2 === 0) {
                filtered.push(arr[i] * arr[i]);
            }
        }
        var sum = 0;
        for (var i = 0; i < filtered.length; i++) {
            sum += filtered[i];
        }
        cache[cacheKey] = sum;
        var keys = Object.keys(cache);
        if (keys.length > MAX_CACHE_SIZE) {
            delete cache[keys[0]];
        }
    }
    var analysis = analyzeValue(a + b);
    var fibIndex = Math.abs(a + b) % FIB_MAX;
    var fibValue = fibonacci(fibIndex);
    var primeCheck = isPrime(Math.abs(a * b) % 100);
    var matrixResult = matrixOperation(a, b);
    this.cached = cache[cacheKey];
    this.fibValue = fibValue;
    this.isPrime = primeCheck;
    this.matrixResult = matrixResult;
    this.analysis = analysis;
    callCount++;
    if (callCount % 10000 === 0) {
        var snapshot = JSON.stringify({
            cacheSize: Object.keys(cache).length,
            stats: stats,
            sampleCount: samples.length
        });
        var len = snapshot.length;
    }
}
var targetFunctions = ['compute_sum', 'compute_sum_heavy', 'compute_sum_complex', 'factorial', 'process_array', 'allocate_and_free', 'test_intercept'];
var counter = 0;
var libfuncs = Process.findModuleByName('libfuncs.so');
if (libfuncs) {
    var exports = libfuncs.enumerateExports();
    targetFunctions.forEach(function (funcName) {
        var funcExport = exports.find(e => e.name === funcName);
        if (funcExport) {
            try {
                var counter = 0;
                Interceptor.attach(funcExport.address, {
                    onEnter: function (args) {
                        if (funcName === 'compute_sum_complex') {
                            this.a = args[0].toInt32();
                            this.b = args[1].toInt32();
                            complexThing.call(this, this.a, this.b);
                        }
                        counter++;
                    },
                    onLeave: function (retval) {
                        counter++;
                        if (funcName === 'test_intercept') {
                            retval.replace(Memory.allocUtf8String('FRIDA_BOTH'));
                        } else {
                            if (funcName === 'compute_sum_complex')
                                complexThing.call(this, this.a, this.b);
                            retval.replace(0x42);
                        }
                    }
                });
            } catch (e) {
            }
        }
    });
}