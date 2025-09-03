#!/usr/bin/env python3
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

plt.style.use('dark_background')

df_timing = pd.read_csv('results/results.csv')
df_memory = pd.read_csv('results/memory.csv')

colors = {
    'baseline': '#00ff41',
    'ldpreload': '#00b4d8',
    'frida_onenter_v8': '#ff4081',
    'frida_onenter_qjs': '#ff69b4',
    'frida_onleave_v8': '#ff6b35',
    'frida_onleave_qjs': '#ffa500',
    'frida_both_v8': '#ff006e',
    'frida_both_qjs': '#dc143c',
    'frida_cmodule': '#ffd700',
    'frida_complex': '#ff1493',
    'baseline_complex': '#32cd32',
    'ldpreload_complex': '#1e90ff',
    'frida_complex_v8': '#ff4500',
    'frida_complex_qjs': '#9932cc'
}

grid_color = '#2a2a2a'

def plot_function_performance(func_name, title, output_file):
    ERROR_MARGIN_THRESHOLD = 5.0
    fig, ax = plt.subplots(figsize=(10, 8))
    
    func_data = df_timing[df_timing['Function'] == func_name]
    
    stats = []
    methods = []
    method_order = ['baseline', 'ldpreload', 'frida_onenter_v8', 'frida_onleave_v8', 'frida_both_v8', 'frida_cmodule', 'frida_complex']
    
    for method in method_order:
        method_data = func_data[func_data['Method'] == method]['Time_us']
        if len(method_data) > 0:
            q1, median, q3 = method_data.quantile([0.25, 0.5, 0.75])
            iqr = q3 - q1
            min_val = method_data.min()
            max_val = method_data.max()
            stats.append({
                'median': median,
                'q1': q1,
                'q3': q3,
                'iqr': iqr,
                'min': min_val,
                'max': max_val,
                'method': method
            })
            methods.append(method)
    
    if stats:
        x_pos = np.arange(len(stats))
        medians = [s['median'] for s in stats]
        yerr_lower = [s['median'] - s['q1'] for s in stats]
        yerr_upper = [s['q3'] - s['median'] for s in stats]
        yerr = [yerr_lower, yerr_upper]
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
            elif m == 'frida_cmodule':
                labels.append('Frida\n(CModule)')
            elif m == 'frida_complex':
                labels.append('Frida\n(Complex)')
        
        bars = ax.bar(x_pos, medians, yerr=yerr, capsize=6, 
                      color=bar_colors, alpha=0.85, 
                      error_kw={'linewidth': 2, 'ecolor': 'white'},
                      width=0.7)
        
        ax.set_title(title, fontsize=16, fontweight='bold', color='#ffffff')
        ax.set_ylabel('Time (μs) - Log Scale', fontsize=12, color='#ffffff')
        ax.set_yscale('log')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, rotation=0, fontsize=10)
        
        ax.grid(True, alpha=0.2, color=grid_color, linestyle='--')
        ax.set_axisbelow(True)
        ax.set_facecolor('#1a1a1a')
        
        baseline_median = next(s['median'] for s in stats if s['method'] == 'baseline')
        
        num_calls = {
            'hot_path': 1000000,
            'heavy_work': 1000000,
            'recursive': 1000000,
            'array_ops': 100000,
            'memory_ops': 1000000
        }.get(func_name, 1000000)
        
        for bar, stat in zip(bars, stats):
            height = bar.get_height()
            
            if stat['method'] == 'baseline':
                label = f"{stat['median']:.1f}μs\n[{stat['q1']:.0f}-{stat['q3']:.0f}]"
                overhead_label = "(baseline)"
            else:
                overhead_pct = ((stat['median'] - baseline_median) / baseline_median * 100) if baseline_median > 0 else 0
                overhead_per_call_us = (stat['median'] - baseline_median) / num_calls
                label = f"{stat['median']:.1f}μs\n[{stat['q1']:.0f}-{stat['q3']:.0f}]"
                if overhead_per_call_us < 1:
                    overhead_per_call_ns = overhead_per_call_us * 1000
                    overhead_label = f"+{overhead_pct:.1f}%\n({overhead_per_call_ns:.1f}ns/call)"
                else:
                    overhead_label = f"+{overhead_pct:.1f}%\n({overhead_per_call_us:.3f}μs/call)"
            
            va = 'bottom'
            y_offset = (stat['q3'] if stat['q3'] > 0 else stat['median']) * 1.15
            
            ax.text(bar.get_x() + bar.get_width()/2, y_offset,
                   label, ha='center', va=va, 
                   fontsize=8, fontweight='bold', color='#ffffff')
            
            if stat['method'] != 'baseline':
                ax.text(bar.get_x() + bar.get_width()/2, y_offset * 1.8,
                       overhead_label, ha='center', va=va,
                       fontsize=7, color='#ffccaa')
        
        y_min = max(1, min([s['q1'] for s in stats]) * 0.8)
        y_max = max([s['q3'] for s in stats]) * 5
        
        ax.set_ylim(y_min, y_max)
        
        baseline_median = next(s['median'] for s in stats if s['method'] == 'baseline')
        ax.axhline(y=baseline_median, color='#00ff41', linestyle='--', linewidth=1, alpha=0.3, label='Baseline median')
        
        error_margin = baseline_median * (ERROR_MARGIN_THRESHOLD / 100)
        ax.axhspan(baseline_median - error_margin, baseline_median + error_margin, 
                  color='yellow', alpha=0.1, label=f'±{ERROR_MARGIN_THRESHOLD}% noise zone')
    
    fig.patch.set_facecolor('#0d0d0d')
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, facecolor='#0d0d0d', edgecolor='none')
    plt.close()
    print(f"Saved: {output_file}")

functions = [
    ('hot_path', 'Hot Path Performance (1M calls)', 'results/performance_hot_path.png'),
    ('heavy_work', 'Heavy Work Performance (1M calls)', 'results/performance_heavy_work.png'),
    ('recursive', 'Recursive Performance (1M calls)', 'results/performance_recursive.png'),
    ('array_ops', 'Array Operations Performance (100K calls)', 'results/performance_array_ops.png'),
    ('memory_ops', 'Memory Operations Performance (1M calls)', 'results/performance_memory_ops.png')
]

for func_name, title, output_file in functions:
    plot_function_performance(func_name, title, output_file)

def plot_runtime_comparison():
    ERROR_MARGIN_THRESHOLD = 5.0
    fig, ax = plt.subplots(figsize=(12, 8))
    
    func_data = df_timing[df_timing['Function'] == 'hot_path']
    
    baseline_data = func_data[func_data['Method'] == 'baseline']['Time_us']
    baseline_median = baseline_data.median() if len(baseline_data) > 0 else 0
    
    stats_runtime = []
    methods_runtime = []
    method_order_runtime = ['baseline', 'ldpreload', 'onenter_v8', 'onenter_qjs', 'onleave_v8', 'onleave_qjs', 'both_v8', 'both_qjs']
    
    for method in method_order_runtime:
        if method in ['baseline', 'ldpreload']:
            method_data = func_data[func_data['Method'] == method]['Time_us']
        else:
            frida_method = f'frida_{method}'
            method_data = func_data[func_data['Method'] == frida_method]['Time_us']
        
        if len(method_data) > 0:
            if method == 'baseline':
                stats_runtime.append({
                    'median': 0,
                    'iqr': 0,
                    'method': method,
                    'original_median': method_data.median()
                })
            else:
                q1, q3 = method_data.quantile([0.25, 0.75])
                iqr = q3 - q1
                stats_runtime.append({
                    'median': method_data.median() - baseline_median,
                    'iqr': iqr,
                    'method': method,
                    'original_median': method_data.median()
                })
            methods_runtime.append(method)
    
    if stats_runtime:
        x_pos = np.arange(len(stats_runtime))
        medians = [s['median'] for s in stats_runtime]
        iqrs = [s['iqr'] for s in stats_runtime]
        yerr = iqrs
        
        runtime_colors = []
        for s in stats_runtime:
            if s['method'] == 'baseline':
                runtime_colors.append(colors['baseline'])
            elif s['method'] == 'ldpreload':
                runtime_colors.append(colors['ldpreload'])
            else:
                frida_key = f"frida_{s['method']}"
                runtime_colors.append(colors.get(frida_key, '#ffffff'))
        
        labels_runtime = []
        for m in methods_runtime:
            if m == 'baseline':
                labels_runtime.append('Baseline\n(Native)')
            elif m == 'ldpreload':
                labels_runtime.append('LD_PRELOAD\n(Hook)')
            else:
                parts = m.split('_')
                mode = parts[0]
                runtime = parts[1].upper() if len(parts) > 1 else 'V8'
                if mode == 'onenter':
                    labels_runtime.append(f'Frida onEnter\n({runtime})')
                elif mode == 'onleave':
                    labels_runtime.append(f'Frida onLeave\n({runtime})')
                elif mode == 'both':
                    labels_runtime.append(f'Frida Both\n({runtime})')
        
        bars = ax.bar(x_pos, medians, yerr=yerr, capsize=6,
                     color=runtime_colors, alpha=0.85,
                     error_kw={'linewidth': 2, 'ecolor': 'white'},
                     width=0.8)
        
        ax.set_title('Runtime Engine Comparison (Hot Path)', fontsize=16, fontweight='bold', color='#ffffff')
        ax.set_ylabel('Overhead (μs) - Log Scale', fontsize=12, color='#ffffff')
        ax.set_yscale('log')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels_runtime, rotation=45, fontsize=10, ha='right')
        
        ax.grid(True, alpha=0.2, color=grid_color, linestyle='--')
        ax.set_axisbelow(True)
        ax.set_facecolor('#1a1a1a')
        
        for bar, stat in zip(bars, stats_runtime):
            height = bar.get_height()
            
            if stat['method'] == 'baseline':
                label = f"{stat['original_median']:.0f}μs\n(baseline)"
            else:
                if stat['median'] >= 0:
                    label = f"+{stat['median']:.0f}μs"
                else:
                    label = f"{stat['median']:.0f}μs"
            
            if height >= 0:
                va = 'bottom'
                y_offset = height + (ax.get_ylim()[1] - ax.get_ylim()[0])*0.02
            else:
                va = 'top'
                y_offset = height - (ax.get_ylim()[1] - ax.get_ylim()[0])*0.02
            
            ax.text(bar.get_x() + bar.get_width()/2, y_offset,
                   label, ha='center', va=va,
                   fontsize=9, fontweight='bold', color='#ffffff')
        
        ax.axhline(y=0, color='#00ff41', linestyle='-', linewidth=1, alpha=0.3)
        
        baseline_median = next(s['original_median'] for s in stats_runtime if s['method'] == 'baseline')
        error_margin = baseline_median * (ERROR_MARGIN_THRESHOLD / 100)
        ax.axhspan(-error_margin, error_margin, 
                  color='yellow', alpha=0.1, label=f'±{ERROR_MARGIN_THRESHOLD}% noise zone')
    
    fig.patch.set_facecolor('#0d0d0d')
    plt.tight_layout()
    plt.savefig('results/performance_runtime_comparison.png', dpi=150, facecolor='#0d0d0d', edgecolor='none')
    plt.close()
    print("Saved: results/performance_runtime_comparison.png")

plot_runtime_comparison()

def plot_memory_usage():
    fig, ax = plt.subplots(figsize=(10, 8))
    
    memory_stats = []
    memory_methods = []
    method_order_memory = ['baseline', 'ldpreload', 'frida_onenter_v8', 'frida_onleave_v8', 'frida_both_v8', 'frida_cmodule', 'frida_complex']
    
    for method in method_order_memory:
        method_data = df_memory[df_memory['Method'] == method]['Memory_KB']
        if len(method_data) > 0:
            q1, q3 = method_data.quantile([0.25, 0.75])
            iqr = q3 - q1
            memory_stats.append({
                'median': method_data.median(),
                'iqr': iqr,
                'method': method
            })
            memory_methods.append(method)
    
    if memory_stats:
        x_pos = np.arange(len(memory_stats))
        medians = [s['median'] for s in memory_stats]
        iqrs = [s['iqr'] for s in memory_stats]
        yerr = iqrs
        bar_colors = [colors[s['method']] for s in memory_stats]
        
        labels_memory = []
        for m in memory_methods:
            if m == 'baseline':
                labels_memory.append('Baseline')
            elif m == 'ldpreload':
                labels_memory.append('LD_PRELOAD')
            elif m == 'frida_onenter_v8':
                labels_memory.append('Frida\n(onEnter)')
            elif m == 'frida_onleave_v8':
                labels_memory.append('Frida\n(onLeave)')
            elif m == 'frida_both_v8':
                labels_memory.append('Frida\n(both)')
            elif m == 'frida_cmodule':
                labels_memory.append('Frida\n(CModule)')
            elif m == 'frida_complex':
                labels_memory.append('Frida\n(Complex)')
        
        bars = ax.bar(x_pos, medians, yerr=yerr, capsize=6,
                      color=bar_colors, alpha=0.85,
                      error_kw={'linewidth': 2, 'ecolor': 'white'},
                      width=0.7)
        
        ax.set_title('Memory Usage Comparison (Log Scale)', fontsize=16, fontweight='bold', color='#ffffff')
        ax.set_ylabel('Memory Usage (KB)', fontsize=12, color='#ffffff')
        ax.set_yscale('log')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels_memory, rotation=0, fontsize=10)
        
        ax.grid(True, alpha=0.2, color=grid_color, linestyle='--', which='both')
        ax.set_axisbelow(True)
        ax.set_facecolor('#1a1a1a')
        
        for bar, stat in zip(bars, memory_stats):
            height = bar.get_height()
            label = f"{stat['median']:.0f}±{stat['iqr']:.0f}KB"
            
            ax.text(bar.get_x() + bar.get_width()/2, height * 1.1,
                   label, ha='center', va='bottom',
                   fontsize=9, fontweight='bold', color='#ffffff')
        
        min_val = min(medians) * 0.8 if min(medians) > 0 else 1
        max_val = max(medians) * 1.5
        ax.set_ylim(min_val, max_val)
    
    fig.patch.set_facecolor('#0d0d0d')
    plt.tight_layout()
    plt.savefig('results/performance_memory.png', dpi=150, facecolor='#0d0d0d', edgecolor='none')
    plt.close()
    print("Saved: results/performance_memory.png")

plot_memory_usage()

def plot_complex_path():
    complex_data = df_timing[df_timing['Function'] == 'complex_ops']
    
    if len(complex_data) == 0:
        print("No complex_ops data found, skipping complex path chart")
        return
    
    stats = []
    methods = []
    method_order = ['baseline_complex', 'ldpreload_complex', 'frida_complex_v8', 'frida_complex_qjs']
    
    for method in method_order:
        method_data = complex_data[complex_data['Method'] == method]['Time_us']
        if len(method_data) > 0:
            q1, median, q3 = method_data.quantile([0.25, 0.5, 0.75])
            iqr = q3 - q1
            stats.append({
                'median': median,
                'q1': q1,
                'q3': q3,
                'iqr': iqr,
                'method': method
            })
            methods.append(method)
    
    if not stats:
        print("No valid complex path data found for plotting")
        return
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    if stats:
        x_pos = np.arange(len(stats))
        medians = [s['median'] for s in stats]
        yerr_lower = [s['median'] - s['q1'] for s in stats]
        yerr_upper = [s['q3'] - s['median'] for s in stats]
        yerr = [yerr_lower, yerr_upper]
        bar_colors = [colors[s['method']] for s in stats]
        
        labels = []
        for m in methods:
            if m == 'baseline_complex':
                labels.append('C Native\n(Complex)')
            elif m == 'ldpreload_complex':
                labels.append('LD_PRELOAD\n(Complex)')
            elif m == 'frida_complex_v8':
                labels.append('Frida V8\n(Complex)')
            elif m == 'frida_complex_qjs':
                labels.append('Frida QuickJS\n(Complex)')
        
        bar_width = 0.6 if len(stats) <= 2 else 0.7
        
        bars = ax.bar(x_pos, medians, yerr=yerr, capsize=6, 
                      color=bar_colors, alpha=0.85, 
                      error_kw={'linewidth': 2, 'ecolor': 'white'},
                      width=bar_width)
        
        if len(stats) == 2:
            ax.set_title('Complex Operations Performance Comparison\n(C Native vs LD_PRELOAD)', 
                         fontsize=14, fontweight='bold', color='#ffffff')
        else:
            ax.set_title('Complex Operations Performance Comparison\n(Baseline C → LD_PRELOAD → Frida V8 → Frida QuickJS)', 
                         fontsize=14, fontweight='bold', color='#ffffff')
        
        ax.set_ylabel('Time (μs)', fontsize=12, color='#ffffff')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, fontsize=11)
        
        padding = 0.5 if len(stats) <= 2 else 0.3
        ax.set_xlim(-padding, len(stats) - 1 + padding)
        
        ax.grid(True, alpha=0.2, color=grid_color, linestyle='--')
        ax.set_axisbelow(True)
        ax.set_facecolor('#1a1a1a')
        
        baseline_median = next((s['median'] for s in stats if s['method'] == 'baseline_complex'), 0)
        
        for bar, stat in zip(bars, stats):
            height = bar.get_height()
            
            if stat['method'] == 'baseline_complex':
                label = f"{stat['median']:.0f}μs\n(baseline)"
            elif stat['method'] == 'ldpreload_complex':
                pct_overhead = ((stat['median'] - baseline_median) / baseline_median * 100)
                label = f"{stat['median']:.0f}μs\n(+{pct_overhead:.1f}%)"
            else:
                overhead_pct = ((stat['median'] - baseline_median) / baseline_median * 100) if baseline_median > 0 else 0
                overhead_per_call_us = (stat['median'] - baseline_median) / 1000000
                
                if overhead_per_call_us < 1:
                    overhead_per_call_ns = overhead_per_call_us * 1000
                    overhead_label = f"+{overhead_pct:.1f}%\n({overhead_per_call_ns:.1f}ns/call)"
                else:
                    overhead_label = f"+{overhead_pct:.1f}%\n({overhead_per_call_us:.3f}μs/call)"
                
                label = f"{stat['median']:.0f}μs\n{overhead_label}"
            
            y_offset = stat['q3'] + (max([s['q3'] for s in stats]) - min(medians)) * 0.02
            
            ax.text(bar.get_x() + bar.get_width()/2, y_offset,
                   label, ha='center', va='bottom', 
                   fontsize=10, fontweight='bold', color='#ffffff')
        
        y_min = min(medians) * 0.98
        y_max = max([s['q3'] for s in stats]) * 1.08
        ax.set_ylim(y_min, y_max)
        
        if baseline_median > 0:
            ax.axhline(y=baseline_median, color='#32cd32', linestyle='--', linewidth=1, alpha=0.3)
    
    fig.patch.set_facecolor('#0d0d0d')
    plt.tight_layout()
    plt.savefig('results/performance_complex_path.png', dpi=150, facecolor='#0d0d0d', edgecolor='none')
    plt.close()
    print("Saved: results/performance_complex_path.png")

plot_complex_path()

def plot_combined_overview():
    fig = plt.figure(figsize=(24, 16))
    
    functions = ['hot_path', 'heavy_work', 'recursive', 'array_ops', 'memory_ops']
    titles = ['Hot Path (1M calls)', 'Heavy Work (1M calls)', 'Recursive (1M calls)', 'Array Ops (100K calls)', 'Memory Ops (1M calls)']
    
    for idx, (func, title) in enumerate(zip(functions, titles)):
        ax = plt.subplot(3, 3, idx + 1)
        func_data = df_timing[df_timing['Function'] == func]
        
        stats = []
        methods = []
        method_order = ['baseline', 'ldpreload', 'frida_onenter_v8', 'frida_onleave_v8', 'frida_both_v8', 'frida_cmodule', 'frida_complex']
        
        baseline_data = func_data[func_data['Method'] == 'baseline']['Time_us']
        baseline_median = baseline_data.median() if len(baseline_data) > 0 else 0
        
        for method in method_order:
            method_data = func_data[func_data['Method'] == method]['Time_us']
            if len(method_data) > 0:
                q1, q3 = method_data.quantile([0.25, 0.75])
                iqr = q3 - q1
                stats.append({
                    'median': method_data.median(),
                    'iqr': iqr,
                    'method': method,
                    'original_median': method_data.median()
                })
                methods.append(method)
        
        if stats:
            x_pos = np.arange(len(stats))
            medians = [s['median'] for s in stats]
            iqrs = [s['iqr'] for s in stats]
            yerr = iqrs
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
                elif m == 'frida_cmodule':
                    labels.append('Frida\n(CModule)')
                elif m == 'frida_complex':
                    labels.append('Frida\n(Complex)')
            
            bars = ax.bar(x_pos, medians, yerr=yerr, capsize=6,
                         color=bar_colors, alpha=0.85,
                         error_kw={'linewidth': 2, 'ecolor': 'white'},
                         width=0.7)
            
            ax.set_title(title, fontsize=12, fontweight='bold', color='#ffffff')
            ax.set_ylabel('Time (μs) - Log Scale', fontsize=10, color='#ffffff')
            ax.set_yscale('log')
            ax.set_xticks(x_pos)
            ax.set_xticklabels(labels, rotation=0, fontsize=8)
            
            ax.grid(True, alpha=0.2, color=grid_color, linestyle='--')
            ax.set_axisbelow(True)
            ax.set_facecolor('#1a1a1a')
            
            for bar, stat in zip(bars, stats):
                height = bar.get_height()
                if stat['method'] == 'baseline':
                    label = f"{stat['median']:.1f}μs\n(baseline)"
                else:
                    label = f"{stat['median']:.1f}±{stat['iqr']:.1f}"
                
                if height >= 0:
                    va = 'bottom'
                    y_offset = height + (ax.get_ylim()[1] - ax.get_ylim()[0])*0.02
                else:
                    va = 'top'
                    y_offset = height - (ax.get_ylim()[1] - ax.get_ylim()[0])*0.02
                
                ax.text(bar.get_x() + bar.get_width()/2, y_offset,
                       label, ha='center', va=va,
                       fontsize=7, fontweight='bold', color='#ffffff')
    
    ax_runtime = plt.subplot(3, 3, 7)
    func_data = df_timing[df_timing['Function'] == 'hot_path']
    baseline_data = func_data[func_data['Method'] == 'baseline']['Time_us']
    baseline_median = baseline_data.median() if len(baseline_data) > 0 else 0
    
    stats_runtime = []
    methods_runtime = []
    method_order_runtime = ['baseline', 'ldpreload', 'onenter_v8', 'onenter_qjs', 'onleave_v8', 'onleave_qjs', 'both_v8', 'both_qjs']
    
    for method in method_order_runtime:
        if method in ['baseline', 'ldpreload']:
            method_data = func_data[func_data['Method'] == method]['Time_us']
        else:
            frida_method = f'frida_{method}'
            method_data = func_data[func_data['Method'] == frida_method]['Time_us']
        
        if len(method_data) > 0:
            if method == 'baseline':
                stats_runtime.append({
                    'median': 0,
                    'iqr': 0,
                    'method': method,
                    'original_median': method_data.median()
                })
            else:
                q1, q3 = method_data.quantile([0.25, 0.75])
                iqr = q3 - q1
                stats_runtime.append({
                    'median': method_data.median() - baseline_median,
                    'iqr': iqr,
                    'method': method,
                    'original_median': method_data.median()
                })
            methods_runtime.append(method)
    
    if stats_runtime:
        x_pos = np.arange(len(stats_runtime))
        medians = [s['median'] for s in stats_runtime]
        iqrs = [s['iqr'] for s in stats_runtime]
        yerr = iqrs
        
        runtime_colors = []
        for s in stats_runtime:
            if s['method'] == 'baseline':
                runtime_colors.append(colors['baseline'])
            elif s['method'] == 'ldpreload':
                runtime_colors.append(colors['ldpreload'])
            else:
                frida_key = f"frida_{s['method']}"
                runtime_colors.append(colors.get(frida_key, '#ffffff'))
        
        labels_runtime = []
        for m in methods_runtime:
            if m == 'baseline':
                labels_runtime.append('Baseline\n(Native)')
            elif m == 'ldpreload':
                labels_runtime.append('LD_PRELOAD\n(Hook)')
            else:
                parts = m.split('_')
                mode = parts[0]
                runtime = parts[1].upper() if len(parts) > 1 else 'V8'
                if mode == 'onenter':
                    labels_runtime.append(f'Frida onEnter\n({runtime})')
                elif mode == 'onleave':
                    labels_runtime.append(f'Frida onLeave\n({runtime})')
                elif mode == 'both':
                    labels_runtime.append(f'Frida Both\n({runtime})')
        
        bars = ax_runtime.bar(x_pos, medians, yerr=yerr, capsize=6,
                             color=runtime_colors, alpha=0.85,
                             error_kw={'linewidth': 2, 'ecolor': 'white'},
                             width=0.8)
        
        ax_runtime.set_title('Runtime Engine Comparison (Hot Path)', fontsize=12, fontweight='bold', color='#ffffff')
        ax_runtime.set_ylabel('Overhead (μs) - Log Scale', fontsize=10, color='#ffffff')
        ax_runtime.set_yscale('log')
        ax_runtime.set_xticks(x_pos)
        ax_runtime.set_xticklabels(labels_runtime, rotation=45, fontsize=8, ha='right')
        
        ax_runtime.grid(True, alpha=0.2, color=grid_color, linestyle='--')
        ax_runtime.set_axisbelow(True)
        ax_runtime.set_facecolor('#1a1a1a')
        
        for bar, stat in zip(bars, stats_runtime):
            height = bar.get_height()
            if stat['method'] == 'baseline':
                label = f"{stat['original_median']:.0f}μs\n(baseline)"
            else:
                if stat['median'] >= 0:
                    label = f"+{stat['median']:.0f}μs"
                else:
                    label = f"{stat['median']:.0f}μs"
            
            if height >= 0:
                va = 'bottom'
                y_offset = height + (ax_runtime.get_ylim()[1] - ax_runtime.get_ylim()[0])*0.02
            else:
                va = 'top'
                y_offset = height - (ax_runtime.get_ylim()[1] - ax_runtime.get_ylim()[0])*0.02
            
            ax_runtime.text(bar.get_x() + bar.get_width()/2, y_offset,
                           label, ha='center', va=va,
                           fontsize=8, fontweight='bold', color='#ffffff')
        
        ax_runtime.axhline(y=0, color='#00ff41', linestyle='-', linewidth=1, alpha=0.3)
    
    ax_memory = plt.subplot(3, 3, (8, 9))
    
    memory_stats = []
    memory_methods = []
    method_order_memory = ['baseline', 'ldpreload', 'frida_onenter_v8', 'frida_onleave_v8', 'frida_both_v8', 'frida_cmodule', 'frida_complex']
    
    for method in method_order_memory:
        method_data = df_memory[df_memory['Method'] == method]['Memory_KB']
        if len(method_data) > 0:
            q1, q3 = method_data.quantile([0.25, 0.75])
            iqr = q3 - q1
            memory_stats.append({
                'median': method_data.median(),
                'iqr': iqr,
                'method': method
            })
            memory_methods.append(method)
    
    if memory_stats:
        x_pos = np.arange(len(memory_stats))
        medians = [s['median'] for s in memory_stats]
        iqrs = [s['iqr'] for s in memory_stats]
        yerr = iqrs
        bar_colors = [colors[s['method']] for s in memory_stats]
        
        labels_memory = []
        for m in memory_methods:
            if m == 'baseline':
                labels_memory.append('Baseline')
            elif m == 'ldpreload':
                labels_memory.append('LD_PRELOAD')
            elif m == 'frida_onenter_v8':
                labels_memory.append('Frida\n(onEnter)')
            elif m == 'frida_onleave_v8':
                labels_memory.append('Frida\n(onLeave)')
            elif m == 'frida_both_v8':
                labels_memory.append('Frida\n(both)')
            elif m == 'frida_cmodule':
                labels_memory.append('Frida\n(CModule)')
            elif m == 'frida_complex':
                labels_memory.append('Frida\n(Complex)')
        
        bars = ax_memory.bar(x_pos, medians, yerr=yerr, capsize=6,
                            color=bar_colors, alpha=0.85,
                            error_kw={'linewidth': 2, 'ecolor': 'white'},
                            width=0.7)
        
        ax_memory.set_title('Memory Usage Comparison (Log Scale)', fontsize=12, fontweight='bold', color='#ffffff')
        ax_memory.set_ylabel('Memory Usage (KB)', fontsize=10, color='#ffffff')
        ax_memory.set_yscale('log')
        ax_memory.set_xticks(x_pos)
        ax_memory.set_xticklabels(labels_memory, rotation=0, fontsize=8)
        
        ax_memory.grid(True, alpha=0.2, color=grid_color, linestyle='--', which='both')
        ax_memory.set_axisbelow(True)
        ax_memory.set_facecolor('#1a1a1a')
        
        for bar, stat in zip(bars, memory_stats):
            height = bar.get_height()
            label = f"{stat['median']:.0f}±{stat['iqr']:.0f}KB"
            ax_memory.text(bar.get_x() + bar.get_width()/2, height * 1.1,
                          label, ha='center', va='bottom',
                          fontsize=8, fontweight='bold', color='#ffffff')
        
        min_val = min(medians) * 0.8 if min(medians) > 0 else 1
        max_val = max(medians) * 1.5
        ax_memory.set_ylim(min_val, max_val)
    
    fig.patch.set_facecolor('#0d0d0d')
    plt.suptitle('C Function Interception Performance & Memory Analysis',
                 fontsize=18, fontweight='bold', color='#ffffff', y=0.98)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig('results/performance.png', dpi=150, facecolor='#0d0d0d', edgecolor='none')
    plt.close()
    print("Saved: results/performance.png (combined overview)")

plot_combined_overview()

print("\nAll charts have been generated successfully!")
print("Individual charts:")
print("  - results/performance_hot_path.png")
print("  - results/performance_heavy_work.png")
print("  - results/performance_recursive.png")
print("  - results/performance_array_ops.png")
print("  - results/performance_memory_ops.png")
print("  - results/performance_runtime_comparison.png")
print("  - results/performance_memory.png")
print("Combined overview:")
print("  - results/performance.png")

print("\n" + "="*80)
print("PERFORMANCE ANALYSIS SUMMARY")
print("="*80)

hot_path_data = df_timing[df_timing['Function'] == 'hot_path']
baseline_hot = hot_path_data[hot_path_data['Method'] == 'baseline']['Time_us'].median()

print(f"\nHot Path Analysis (1M calls, baseline: {baseline_hot:.0f} μs):")
print("-" * 50)

methods_to_analyze = ['ldpreload', 'frida_onenter_v8', 'frida_onleave_v8', 'frida_both_v8', 'frida_cmodule', 'frida_complex']
complex_methods_to_analyze = ['baseline_complex', 'frida_complex_v8', 'frida_complex_qjs']
for method in methods_to_analyze:
    method_data = hot_path_data[hot_path_data['Method'] == method]['Time_us']
    if len(method_data) > 0:
        median = method_data.median()
        overhead_us = median - baseline_hot
        overhead_pct = (overhead_us / baseline_hot * 100) if baseline_hot > 0 else 0
        overhead_per_call_us = overhead_us / 1000000
        
        method_display = {
            'ldpreload': 'LD_PRELOAD',
            'frida_onenter_v8': 'Frida onEnter (V8)',
            'frida_onleave_v8': 'Frida onLeave (V8)',
            'frida_both_v8': 'Frida Both (V8)',
            'frida_cmodule': 'Frida CModule',
            'frida_complex': 'Frida Complex (V8)'
        }.get(method, method)
        
        if overhead_per_call_us < 0.001:
            overhead_per_call_ns = overhead_per_call_us * 1000
            print(f"  {method_display:20s}: +{overhead_us:7.0f} μs (+{overhead_pct:7.1f}%) = {overhead_per_call_ns:7.1f} ns/call")
        else:
            print(f"  {method_display:20s}: +{overhead_us:7.0f} μs (+{overhead_pct:7.1f}%) = {overhead_per_call_us:7.3f} μs/call")

print(f"\nMemory Usage Analysis:")
print("-" * 50)
baseline_mem = df_memory[df_memory['Method'] == 'baseline']['Memory_KB'].median()
print(f"  Baseline: {baseline_mem:.0f} KB")

for method in methods_to_analyze:
    method_data = df_memory[df_memory['Method'] == method]['Memory_KB']
    if len(method_data) > 0:
        median = method_data.median()
        overhead_kb = median - baseline_mem
        overhead_pct = (overhead_kb / baseline_mem * 100) if baseline_mem > 0 else 0
        
        method_display = {
            'ldpreload': 'LD_PRELOAD',
            'frida_onenter_v8': 'Frida onEnter (V8)',
            'frida_onleave_v8': 'Frida onLeave (V8)',
            'frida_both_v8': 'Frida Both (V8)',
            'frida_cmodule': 'Frida CModule',
            'frida_complex': 'Frida Complex (V8)'
        }.get(method, method)
        
        print(f"  {method_display:20s}: {median:6.0f} KB (+{overhead_kb:6.0f} KB, +{overhead_pct:5.1f}%)")

complex_data = df_timing[df_timing['Function'] == 'complex_ops']
if len(complex_data) > 0:
    baseline_complex = complex_data[complex_data['Method'] == 'baseline_complex']['Time_us'].median()
    
    print(f"\nComplex Operations Analysis (1M calls, C baseline: {baseline_complex:.0f} μs):")
    print("-" * 60)
    
    for method in complex_methods_to_analyze:
        method_data = complex_data[complex_data['Method'] == method]['Time_us']
        if len(method_data) > 0:
            median = method_data.median()
            if method == 'baseline_complex':
                overhead_us = 0
                overhead_pct = 0
                overhead_per_call_us = 0
            else:
                overhead_us = median - baseline_complex
                overhead_pct = (overhead_us / baseline_complex * 100) if baseline_complex > 0 else 0
                overhead_per_call_us = overhead_us / 1000000
            
            method_display = {
                'baseline_complex': 'C Native (Complex)',
                'frida_complex_v8': 'Frida Complex V8', 
                'frida_complex_qjs': 'Frida Complex QuickJS'
            }.get(method, method)
            
            if method == 'baseline_complex':
                print(f"  {method_display:25s}: {median:10.0f} μs (baseline)")
            elif overhead_per_call_us < 1:
                overhead_per_call_ns = overhead_per_call_us * 1000
                print(f"  {method_display:25s}: {median:10.0f} μs (+{overhead_pct:7.1f}%) = {overhead_per_call_ns:7.1f} ns/call")
            else:
                print(f"  {method_display:25s}: {median:10.0f} μs (+{overhead_pct:7.1f}%) = {overhead_per_call_us:7.3f} μs/call")

print("="*80)