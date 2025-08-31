var targetFunctions = ['compute_sum', 'factorial', 'process_array', 'allocate_and_free', 'test_intercept'];

var mainModule = Process.findModuleByName('benchmark');
if (mainModule) {
    var exports = mainModule.enumerateExports();
    
    targetFunctions.forEach(function(funcName) {
        var found = exports.filter(function(exp) { return exp.name === funcName; });
        if (found.length > 0) {
            try {
                Interceptor.attach(found[0].address, {
                    onEnter: function(args) {
                        var result = 0;
                        for (var i = 0; i < 1000000; i++) {
                            result += i * i;
                            result ^= (result << 1);
                        }
                    },
                    onLeave: function(retval) {
                        if (funcName === 'test_intercept') {
                            retval.replace(Memory.allocUtf8String('FRIDA_HOOKED'));
                        }
                    }
                });
            } catch(e) {
            }
        }
    });
}