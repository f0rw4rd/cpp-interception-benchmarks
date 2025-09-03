var targetFunctions = ['compute_sum', 'compute_sum_heavy', 'compute_sum_complex', 'factorial', 'process_array', 'allocate_and_free', 'test_intercept'];
var counter = 0;
var libfuncs = Process.findModuleByName('libfuncs.so');
if (libfuncs) {
    var exports = libfuncs.enumerateExports();
    targetFunctions.forEach(function (funcName) {
        var funcExport = exports.find(e => e.name === funcName);
        if (funcExport) {
            try {
                Interceptor.attach(funcExport.address, {
                    onLeave: function (retval) {
                        counter++;
                        if (funcName === 'test_intercept') {
                            retval.replace(Memory.allocUtf8String('FRIDA_ONLEAVE'));
                        } else {
                            retval.replace(0x42);
                        }
                    }
                });
            } catch (e) {
            }
        }
    });
}