console.log("Script loaded");
var libfuncs = Process.findModuleByName('libfuncs.so');
console.log("libfuncs module:", libfuncs);
if (libfuncs) {
    var exports = libfuncs.enumerateExports();
    console.log("Found", exports.length, "exports");
    var compute_sum_complex = exports.find(function(e) { return e.name === 'compute_sum_complex'; });
    if (compute_sum_complex) {
        console.log("Found compute_sum_complex at", compute_sum_complex.address);
        Interceptor.attach(compute_sum_complex.address, {
            onEnter: function(args) {
                console.log("compute_sum_complex called with", args[0].toInt32(), args[1].toInt32());
            },
            onLeave: function(retval) {
                console.log("compute_sum_complex returning", retval.toInt32());
                retval.replace(0x42);
            }
        });
    }
}
