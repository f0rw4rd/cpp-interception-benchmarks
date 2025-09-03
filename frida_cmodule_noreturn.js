const cm = new CModule(`
#include <gum/guminterceptor.h>
int counter = 0;
void onEnter(GumInvocationContext *ic) {
}
void onLeave(GumInvocationContext *ic) {
}
`);
var targetFunctions = ['compute_sum', 'compute_sum_heavy', 'compute_sum_complex', 'factorial', 'process_array', 'allocate_and_free', 'test_intercept'];
var hooked = 0;
function hookFunctions() {
    var libfuncs = Process.findModuleByName('libfuncs.so');
    if (libfuncs) {
        var exports = libfuncs.enumerateExports();
        targetFunctions.forEach(function (funcName) {
            var funcExport = exports.find(e => e.name === funcName);
            if (funcExport) {
                try {
                    Interceptor.attach(funcExport.address, {
                        onEnter: cm.onEnter,
                        onLeave: cm.onLeave
                    });
                    hooked++;
                    console.log(`Hooked ${funcName} at ${funcExport.address}`);
                } catch (e) {
                    console.log(`Failed to hook ${funcName}: ${e}`);
                }
            }
        });
        console.log(`CModule hooks installed (no return modification) - hooked ${hooked} functions`);
    } else {
        setTimeout(hookFunctions, 10);
    }
}
hookFunctions();