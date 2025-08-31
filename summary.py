#!/usr/bin/env python3
import pandas as pd

df = pd.read_csv('results.csv')
print('Performance Summary (mean ± std ms):\n')

methods_to_show = [
    'baseline', 'ldpreload', 
    'frida_onenter_v8', 'frida_onleave_v8', 'frida_both_v8',
    'frida_onenter_qjs', 'frida_onleave_qjs', 'frida_both_qjs'
]

for func in df['Function'].unique():
    print(f'{func.upper()}:')
    for method in methods_to_show:
        data = df[(df['Function']==func) & (df['Method']==method)]['Time_ms']
        if len(data) > 0:
            if method == 'baseline':
                label = 'Baseline'
            elif method == 'ldpreload':
                label = 'LD_PRELOAD'
            else:
                parts = method.split('_')
                mode = parts[1]
                runtime = parts[2].upper()
                label = f'Frida {mode} ({runtime})'
            print(f'  {label:20}: {data.mean():6.1f} ± {data.std():4.1f}')
    print()

print('\nV8 vs QuickJS Runtime Comparison:')
for func in df['Function'].unique():
    print(f'\n{func.upper()}:')
    for mode in ['onenter', 'onleave', 'both']:
        v8_data = df[(df['Function']==func) & (df['Method']==f'frida_{mode}_v8')]['Time_ms']
        qjs_data = df[(df['Function']==func) & (df['Method']==f'frida_{mode}_qjs')]['Time_ms']
        
        if len(v8_data) > 0 and len(qjs_data) > 0:
            v8_mean = v8_data.mean()
            qjs_mean = qjs_data.mean()
            diff_pct = ((qjs_mean - v8_mean) / v8_mean) * 100
            faster = 'V8' if v8_mean < qjs_mean else 'QuickJS'
            print(f'  {mode:8}: V8={v8_mean:5.1f}ms, QJS={qjs_mean:5.1f}ms ({faster} faster by {abs(diff_pct):4.1f}%)')