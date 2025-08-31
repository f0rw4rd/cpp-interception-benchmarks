#!/usr/bin/env python3
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

plt.style.use('dark_background')

df = pd.read_csv('results.csv')

fig, ax = plt.subplots(1, 1, figsize=(12, 8))

functions = ['hot_path']
titles = ['Hot Path Performance: V8 vs QuickJS']

colors = {
    'onenter_v8': '#00ff41',
    'onenter_qjs': '#7fff00',
    'onleave_v8': '#ff4081',
    'onleave_qjs': '#ff69b4',
    'both_v8': '#ff006e',
    'both_qjs': '#dc143c'
}

grid_color = '#2a2a2a'

for idx, (func, title) in enumerate(zip(functions, titles)):
    func_data = df[df['Function'] == func]
    
    stats = []
    methods = []
    method_order = ['onenter_v8', 'onenter_qjs', 'onleave_v8', 'onleave_qjs', 'both_v8', 'both_qjs']
    
    for method in method_order:
        frida_method = f'frida_{method}'
        method_data = func_data[func_data['Method'] == frida_method]['Time_ms']
        if len(method_data) > 0:
            stats.append({
                'mean': method_data.mean(),
                'std': method_data.std(),
                'method': method
            })
            methods.append(method)
    
    if stats:
        x_pos = np.arange(len(stats))
        means = [s['mean'] for s in stats]
        stds = [s['std'] for s in stats]
        bar_colors = [colors[s['method']] for s in stats]
        
        labels = []
        for m in methods:
            parts = m.split('_')
            mode = parts[0]
            runtime = parts[1].upper()
            if mode == 'onenter':
                labels.append(f'onEnter\n({runtime})')
            elif mode == 'onleave':
                labels.append(f'onLeave\n({runtime})')
            elif mode == 'both':
                labels.append(f'Both\n({runtime})')
        
        bars = ax.bar(x_pos, means, yerr=stds, capsize=6, 
                      color=bar_colors, alpha=0.85, 
                      error_kw={'linewidth': 2, 'ecolor': 'white'},
                      width=0.8)
        
        ax.set_title(title, fontsize=14, fontweight='bold', color='#ffffff')
        ax.set_ylabel('Time (ms)', fontsize=11, color='#ffffff')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, rotation=0, fontsize=9)
        
        ax.grid(True, alpha=0.2, color=grid_color, linestyle='--')
        ax.set_axisbelow(True)
        
        ax.set_facecolor('#1a1a1a')
        
        for bar, mean in zip(bars, means):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + ax.get_ylim()[1]*0.02,
                   f'{mean:.0f}', ha='center', va='bottom', 
                   fontsize=9, fontweight='bold', color='#ffffff')
        
        y_max = max(means) + max(stds) if stds else max(means)
        ax.set_ylim(0, y_max * 1.2)

fig.patch.set_facecolor('#0d0d0d')
plt.suptitle('Frida Runtime Comparison: V8 vs QuickJS', 
             fontsize=16, fontweight='bold', color='#ffffff', y=0.98)



plt.tight_layout(rect=[0, 0, 1, 0.92])
plt.savefig('runtime_comparison.png', dpi=150, facecolor='#0d0d0d', edgecolor='none')
print("Runtime comparison chart saved as runtime_comparison.png")