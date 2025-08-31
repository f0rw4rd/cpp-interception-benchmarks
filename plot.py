#!/usr/bin/env python3
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

plt.style.use('dark_background')

df = pd.read_csv('results.csv')

fig, axes = plt.subplots(2, 2, figsize=(16, 11))
axes = axes.flatten()

functions = ['hot_path', 'recursive', 'array_ops', 'memory_ops']
titles = ['Hot Path (100M calls)', 'Recursive (1M)', 'Array Ops (100K)', 'Memory Ops (1M)']

colors = {
    'baseline': '#00ff41',
    'ldpreload': '#00b4d8',
    'frida_onenter_v8': '#ff4081',
    'frida_onleave_v8': '#ff6b35',
    'frida_both_v8': '#ff006e'
}

grid_color = '#2a2a2a'

for idx, (func, title) in enumerate(zip(functions, titles)):
    ax = axes[idx]
    func_data = df[df['Function'] == func]
    
    stats = []
    methods = []
    method_order = ['baseline', 'ldpreload', 'frida_onenter_v8', 'frida_onleave_v8', 'frida_both_v8']
    
    for method in method_order:
        method_data = func_data[func_data['Method'] == method]['Time_ms']
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
            if m == 'baseline':
                labels.append('Baseline')
            elif m == 'ldpreload':
                labels.append('LD_PRELOAD')
            elif m == 'frida_onenter_v8':
                labels.append('Frida\n(onEnter)')
            elif m == 'frida_onleave_v8':
                labels.append('Frida\n(onLeave)')
            elif m == 'frida_both_v8':
                labels.append('Frida\n(both)')
        
        bars = ax.bar(x_pos, means, yerr=stds, capsize=6, 
                      color=bar_colors, alpha=0.85, 
                      error_kw={'linewidth': 2, 'ecolor': 'white'},
                      width=0.7)
        
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
                   f'{mean:.1f}', ha='center', va='bottom', 
                   fontsize=9, fontweight='bold', color='#ffffff')
        
        y_max = max(means) + max(stds) if stds else max(means)
        ax.set_ylim(0, y_max * 1.2)

fig.patch.set_facecolor('#0d0d0d')
plt.suptitle('C Function Interception Performance Comparison', 
             fontsize=16, fontweight='bold', color='#ffffff', y=0.98)


plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig('performance.png', dpi=150, facecolor='#0d0d0d', edgecolor='none')
print("Chart saved as performance.png")