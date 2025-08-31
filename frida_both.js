var targetFunctions = ['compute_sum', 'factorial', 'process_array', 'allocate_and_free', 'test_intercept'];
var hookCount = 0;

var mainModule = Process.findModuleByName('benchmark');
if (mainModule) {
    var exports = mainModule.enumerateExports();
    console.log('[*] Found ' + exports.length + ' exports');
    
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
                        var result = 0;
                        for (var i = 0; i < 1000000; i++) {
                            result += i * i;
                            result ^= (result << 1);
                        }
                        
                        if (funcName === 'test_intercept') {
                            retval.replace(Memory.allocUtf8String('FRIDA_HOOKED'));
                        }
                    }
                });
                hookCount++;
                console.log('[+] Hooked ' + funcName + ' at ' + found[0].address);
            } catch(e) {
                console.log('[-] Failed to hook ' + funcName + ': ' + e.message);
            }
        } else {
            console.log('[-] Function ' + funcName + ' not found');
        }
    });
    
    console.log('[*] Successfully hooked ' + hookCount + '/' + targetFunctions.length + ' functions');
} else {
    console.log('[-] benchmark module not found');
}