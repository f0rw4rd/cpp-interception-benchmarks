#!/bin/bash

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "Building..."
gcc -o benchmark benchmark.c -rdynamic
gcc -shared -fPIC -o hook.so hook.c

echo "Method,Function,Time_ms" > results.csv

echo
echo "Running benchmarks (10 iterations each)..."

for i in {1..10}; do
    echo -ne "\rBaseline: $i/10"
    output=$(./benchmark 2>/dev/null)
    hot=$(echo "$output" | grep "Hot path:" | awk '{print $3}')
    rec=$(echo "$output" | grep "Recursive:" | awk '{print $2}')
    arr=$(echo "$output" | grep "Array ops:" | awk '{print $3}')
    mem=$(echo "$output" | grep "Memory ops:" | awk '{print $3}')
    
    echo "baseline,hot_path,$hot" >> results.csv
    echo "baseline,recursive,$rec" >> results.csv
    echo "baseline,array_ops,$arr" >> results.csv
    echo "baseline,memory_ops,$mem" >> results.csv
done

echo
for i in {1..10}; do
    echo -ne "\rLD_PRELOAD: $i/10"
    output=$(LD_PRELOAD=./hook.so ./benchmark 2>/dev/null)
    hot=$(echo "$output" | grep "Hot path:" | awk '{print $3}')
    rec=$(echo "$output" | grep "Recursive:" | awk '{print $2}')
    arr=$(echo "$output" | grep "Array ops:" | awk '{print $3}')
    mem=$(echo "$output" | grep "Memory ops:" | awk '{print $3}')
    
    echo "ldpreload,hot_path,$hot" >> results.csv
    echo "ldpreload,recursive,$rec" >> results.csv
    echo "ldpreload,array_ops,$arr" >> results.csv
    echo "ldpreload,memory_ops,$mem" >> results.csv
done

if command -v frida &> /dev/null; then
    echo
    echo "Running Frida benchmarks..."
    
    for runtime in "v8" "qjs"; do
        echo
        echo "Testing runtime: $runtime"
        
        for mode in "onenter" "onleave" "both"; do
            echo "  Testing Frida mode: $mode"
            
            script_file="frida_${mode}.js"
            
            for i in {1..5}; do
                echo -ne "\r  Frida ($mode $runtime): $i/5"
                output=$(frida -l "$script_file" -f ./benchmark --runtime=$runtime -q 2>&1 | tail -n +2)
                
                if [ ! -z "$output" ]; then
                    hot=$(echo "$output" | grep "Hot path:" | awk '{print $3}')
                    rec=$(echo "$output" | grep "Recursive:" | awk '{print $2}')
                    arr=$(echo "$output" | grep "Array ops:" | awk '{print $3}')
                    mem=$(echo "$output" | grep "Memory ops:" | awk '{print $3}')
                    
                    # Only record if all values are present and numeric
                    if [[ "$hot" =~ ^[0-9]+$ && "$rec" =~ ^[0-9]+$ && "$arr" =~ ^[0-9]+$ && "$mem" =~ ^[0-9]+$ ]]; then
                        echo "frida_${mode}_${runtime},hot_path,$hot" >> results.csv
                        echo "frida_${mode}_${runtime},recursive,$rec" >> results.csv
                        echo "frida_${mode}_${runtime},array_ops,$arr" >> results.csv
                        echo "frida_${mode}_${runtime},memory_ops,$mem" >> results.csv
                    else
                        echo "  Warning: Incomplete data for run $i (hot=$hot, rec=$rec, arr=$arr, mem=$mem)"
                    fi
                fi
            done
            echo
        done
    done
else
    echo
    echo "Frida not found. Install with: pip install frida-tools"
fi

echo
echo
echo "Generating plots..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
    python plot.py
    python plot_runtime_comparison.py
else
    python3 plot.py
    python3 plot_runtime_comparison.py
fi

echo "Done! See performance.png and runtime_comparison.png"