#!/bin/bash

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

mkdir -p build results

# Check if results.csv exists and has data BEFORE building
if [ -f "results/results.csv" ] && [ -s "results/results.csv" ]; then
    echo "Found existing results.csv, will resume after build..."
    RESUME=true
    # Backup existing results before building
    cp results/results.csv results/results.csv.backup
    if [ -f "results/memory.csv" ]; then
        cp results/memory.csv results/memory.csv.backup
    fi
else
    echo "No existing results found, will start fresh..."
    RESUME=false
fi

echo "Building..."
make clean
make all

# Restore backups if resuming
if [ "$RESUME" = true ]; then
    if [ -f "results/results.csv.backup" ]; then
        mv results/results.csv.backup results/results.csv
        echo "Restored existing results.csv"
    fi
    if [ -f "results/memory.csv.backup" ]; then
        mv results/memory.csv.backup results/memory.csv
        echo "Restored existing memory.csv"
    fi
else
    echo "Starting fresh benchmark run..."
    echo "Method,Function,Time_us" > results/results.csv
    echo "Method,Memory_KB" > results/memory.csv
fi

# Function to check if a benchmark has been completed
check_benchmark_complete() {
    local method=$1
    local expected_count=$2
    if [ "$RESUME" = true ]; then
        local count=$(grep "^$method," results/results.csv 2>/dev/null | wc -l)
        if [ "$count" -ge "$expected_count" ]; then
            return 0  # Already complete
        else
            return 1  # Not complete
        fi
    else
        return 1  # Not resuming, run everything
    fi
}

echo
echo "Running benchmarks (10 iterations each)..."

# Baseline benchmark
if check_benchmark_complete "baseline" 50; then
    echo "Baseline benchmark already complete, skipping..."
else
    echo "Running baseline benchmark..."
    # Calculate how many iterations are already done
    existing_baseline=$(grep "^baseline," results/results.csv 2>/dev/null | wc -l)
    if [ "$existing_baseline" -eq 0 ]; then
        start_iter=1
    else
        start_iter=$(( (existing_baseline / 5) + 1 ))
    fi
    
    for i in $(seq $start_iter 10); do
        echo -ne "\rBaseline: $i/10"
        output=$(SKIP_INTERCEPT_VALIDATION=1 ./build/benchmark 2>&1)
        if [ $? -gt 0 ]; then
            echo
            echo "Benchmark failed with exit code $?"
            exit 1
        fi
        
        hot=$(echo "$output" | grep "Hot path:" | awk '{print $3}')
        heavy=$(echo "$output" | grep "Heavy work:" | awk '{print $3}')
        rec=$(echo "$output" | grep "Recursive:" | awk '{print $2}')
        arr=$(echo "$output" | grep "Array ops:" | awk '{print $3}')
        mem=$(echo "$output" | grep "Memory ops:" | awk '{print $3}')
        memory=$(echo "$output" | grep "Max memory:" | awk '{print $3}')
        
        echo "baseline,hot_path,$hot" >> results/results.csv
        echo "baseline,heavy_work,$heavy" >> results/results.csv
        echo "baseline,recursive,$rec" >> results/results.csv
        echo "baseline,array_ops,$arr" >> results/results.csv
        echo "baseline,memory_ops,$mem" >> results/results.csv
        echo "baseline,$memory" >> results/memory.csv
    done
    echo
fi

# LD_PRELOAD benchmark
if check_benchmark_complete "ldpreload" 50; then
    echo "LD_PRELOAD benchmark already complete, skipping..."
else
    echo "Running LD_PRELOAD benchmark..."
    existing_ldpreload=$(grep "^ldpreload," results/results.csv 2>/dev/null | wc -l)
    if [ "$existing_ldpreload" -eq 0 ]; then
        start_iter=1
    else
        start_iter=$(( (existing_ldpreload / 5) + 1 ))
    fi
    
    for i in $(seq $start_iter 10); do
        echo -ne "\rLD_PRELOAD: $i/10"
        output=$(LD_PRELOAD=./build/hook.so ./build/benchmark 2>&1)
        if [ $? -gt 0 ]; then
            echo
            echo "LD_PRELOAD benchmark failed with exit code $?"
            exit 1
        fi
        
        hot=$(echo "$output" | grep "Hot path:" | awk '{print $3}')
        heavy=$(echo "$output" | grep "Heavy work:" | awk '{print $3}')
        rec=$(echo "$output" | grep "Recursive:" | awk '{print $2}')
        arr=$(echo "$output" | grep "Array ops:" | awk '{print $3}')
        mem=$(echo "$output" | grep "Memory ops:" | awk '{print $3}')
        memory=$(echo "$output" | grep "Max memory:" | awk '{print $3}')
        
        echo "ldpreload,hot_path,$hot" >> results/results.csv
        echo "ldpreload,heavy_work,$heavy" >> results/results.csv
        echo "ldpreload,recursive,$rec" >> results/results.csv
        echo "ldpreload,array_ops,$arr" >> results/results.csv
        echo "ldpreload,memory_ops,$mem" >> results/results.csv
        echo "ldpreload,$memory" >> results/memory.csv
    done
    echo
fi

if command -v frida &> /dev/null; then
    echo
    echo "Running Frida benchmarks..."
    
    for runtime in "v8" "qjs"; do
        for mode in "onenter" "onleave" "both"; do
            method_name="frida_${mode}_${runtime}"
            
            if check_benchmark_complete "$method_name" 50; then
                echo "Frida $mode $runtime benchmark already complete, skipping..."
            else
                echo "Testing Frida mode: $mode (runtime: $runtime)"
                script_file="frida_${mode}.js"
                
                existing_count=$(grep "^$method_name," results/results.csv 2>/dev/null | wc -l)
                if [ "$existing_count" -eq 0 ]; then
                    start_iter=1
                else
                    start_iter=$(( (existing_count / 5) + 1 ))
                fi
                
                for i in $(seq $start_iter 10); do
                    echo -ne "\r  Frida ($mode $runtime): $i/10"
                    output=$(frida -l "$script_file" -f ./build/benchmark --runtime=$runtime 2>&1 | tail -n +2)
                    frida_exit_code=${PIPESTATUS[0]}
                    if [ $frida_exit_code -gt 0 ]; then
                        echo
                        echo "Frida ($mode $runtime) failed with exit code $frida_exit_code"
                        exit 1
                    fi
                    
                    if [ ! -z "$output" ]; then
                        hot=$(echo "$output" | grep "Hot path:" | awk '{print $3}')
                        heavy=$(echo "$output" | grep "Heavy work:" | awk '{print $3}')
                        rec=$(echo "$output" | grep "Recursive:" | awk '{print $2}')
                        arr=$(echo "$output" | grep "Array ops:" | awk '{print $3}')
                        mem=$(echo "$output" | grep "Memory ops:" | awk '{print $3}')
                        memory=$(echo "$output" | grep "Max memory:" | awk '{print $3}')
                        
                        # Check for hook failure in output
                        if echo "$output" | grep -q "HOOK_FAILURE"; then
                            echo "  Hook failure detected for run $i, skipping"
                            continue
                        fi
                        
                        # Only record if all values are present and numeric
                        if [[ "$hot" =~ ^[0-9]+$ && "$heavy" =~ ^[0-9]+$ && "$rec" =~ ^[0-9]+$ && "$arr" =~ ^[0-9]+$ && "$mem" =~ ^[0-9]+$ && "$memory" =~ ^[0-9]+$ ]]; then
                            echo "frida_${mode}_${runtime},hot_path,$hot" >> results/results.csv
                            echo "frida_${mode}_${runtime},heavy_work,$heavy" >> results/results.csv
                            echo "frida_${mode}_${runtime},recursive,$rec" >> results/results.csv
                            echo "frida_${mode}_${runtime},array_ops,$arr" >> results/results.csv
                            echo "frida_${mode}_${runtime},memory_ops,$mem" >> results/results.csv
                            echo "frida_${mode}_${runtime},$memory" >> results/memory.csv
                        else
                            echo "  Warning: Incomplete data for run $i (hot=$hot, heavy=$heavy, rec=$rec, arr=$arr, mem=$mem, memory=$memory)"
                        fi
                    fi
                done
                echo
            fi
        done
    done
    
    # Add CModule benchmark (V8 only, no QuickJS support)
    if check_benchmark_complete "frida_cmodule" 50; then
        echo "Frida CModule benchmark already complete, skipping..."
    else
        echo
        echo "Testing Frida CModule (native callbacks)..."
        existing_cmodule=$(grep "^frida_cmodule," results/results.csv 2>/dev/null | wc -l)
        if [ "$existing_cmodule" -eq 0 ]; then
            start_iter=1
        else
            start_iter=$(( (existing_cmodule / 5) + 1 ))
        fi
        
        for i in $(seq $start_iter 10); do
            echo -ne "\r  Frida CModule: $i/10"
            output=$(SKIP_INTERCEPT_VALIDATION=1 frida -l frida_cmodule_noreturn.js -f ./build/benchmark 2>&1 | tail -n +2)
            frida_exit_code=${PIPESTATUS[0]}
            if [ $frida_exit_code -gt 0 ]; then
                echo
                echo "Frida CModule failed with exit code $frida_exit_code"
                exit 1
            fi
            
            if [ ! -z "$output" ]; then
                hot=$(echo "$output" | grep "Hot path:" | awk '{print $3}')
                heavy=$(echo "$output" | grep "Heavy work:" | awk '{print $3}')
                rec=$(echo "$output" | grep "Recursive:" | awk '{print $2}')
                arr=$(echo "$output" | grep "Array ops:" | awk '{print $3}')
                mem=$(echo "$output" | grep "Memory ops:" | awk '{print $3}')
                memory=$(echo "$output" | grep "Max memory:" | awk '{print $3}')
                
                # Only record if all values are present and numeric
                if [[ "$hot" =~ ^[0-9]+$ && "$heavy" =~ ^[0-9]+$ && "$rec" =~ ^[0-9]+$ && "$arr" =~ ^[0-9]+$ && "$mem" =~ ^[0-9]+$ && "$memory" =~ ^[0-9]+$ ]]; then
                    echo "frida_cmodule,hot_path,$hot" >> results/results.csv
                    echo "frida_cmodule,heavy_work,$heavy" >> results/results.csv
                    echo "frida_cmodule,recursive,$rec" >> results/results.csv
                    echo "frida_cmodule,array_ops,$arr" >> results/results.csv
                    echo "frida_cmodule,memory_ops,$mem" >> results/results.csv
                    echo "frida_cmodule,$memory" >> results/memory.csv
                else
                    echo "  Warning: Incomplete data for run $i (hot=$hot, heavy=$heavy, rec=$rec, arr=$arr, mem=$mem, memory=$memory)"
                fi
            fi
        done
        echo
    fi
    
    # Complex Path Benchmarks - Comprehensive comparison
    echo
    echo "==============================================="
    echo "COMPLEX PATH ANALYSIS:"
    echo "Baseline → C Complex → Frida V8 → Frida QuickJS"
    echo "==============================================="
    
    # 1. Baseline with C Complex Operations
    if check_benchmark_complete "baseline_complex" 10; then
        echo "Baseline complex benchmark already complete, skipping..."
    else
        echo
        echo "Testing C Complex Operations (baseline)..."
        existing_baseline_complex=$(grep "^baseline_complex," results/results.csv 2>/dev/null | wc -l)
        start_iter=$((existing_baseline_complex + 1))
        
        for i in $(seq $start_iter 10); do
            echo -ne "\r  C Complex: $i/10"
            output=$(SKIP_INTERCEPT_VALIDATION=1 ./build/benchmark 2>&1)
            if [ $? -gt 0 ]; then
                echo
                echo "C Complex benchmark failed"
                exit 1
            fi
            
            if [ ! -z "$output" ]; then
                complex=$(echo "$output" | grep "Complex ops:" | awk '{print $3}')
                memory=$(echo "$output" | grep "Max memory:" | awk '{print $3}')
                
                if [[ "$complex" =~ ^[0-9]+$ && "$memory" =~ ^[0-9]+$ ]]; then
                    echo "baseline_complex,complex_ops,$complex" >> results/results.csv
                    echo "baseline_complex,$memory" >> results/memory.csv
                else
                    echo "  Warning: Incomplete data for run $i (complex=$complex, memory=$memory)"
                fi
            fi
        done
        echo
    fi
    
    # 2. LD_PRELOAD with C Complex Operations
    if check_benchmark_complete "ldpreload_complex" 10; then
        echo "LD_PRELOAD complex benchmark already complete, skipping..."
    else
        echo
        echo "Testing LD_PRELOAD Complex Operations..."
        existing_ldpreload_complex=$(grep "^ldpreload_complex," results/results.csv 2>/dev/null | wc -l)
        start_iter=$((existing_ldpreload_complex + 1))
        
        for i in $(seq $start_iter 10); do
            echo -ne "\r  LD_PRELOAD Complex: $i/10"
            output=$(LD_PRELOAD=./build/hook.so ./build/benchmark 2>&1)
            if [ $? -gt 0 ]; then
                echo
                echo "LD_PRELOAD Complex benchmark failed"
                exit 1
            fi
            
            if [ ! -z "$output" ]; then
                complex=$(echo "$output" | grep "Complex ops:" | awk '{print $3}')
                memory=$(echo "$output" | grep "Max memory:" | awk '{print $3}')
                
                if [[ "$complex" =~ ^[0-9]+$ && "$memory" =~ ^[0-9]+$ ]]; then
                    echo "ldpreload_complex,complex_ops,$complex" >> results/results.csv
                    echo "ldpreload_complex,$memory" >> results/memory.csv
                else
                    echo "  Warning: Incomplete data for run $i (complex=$complex, memory=$memory)"
                fi
            fi
        done
        echo
    fi
    
    # 3. Frida Complex with different runtimes
    for runtime in "v8" "qjs"; do
        method_name="frida_complex_${runtime}"
        
        if check_benchmark_complete "$method_name" 10; then
            echo "Frida complex $runtime benchmark already complete, skipping..."
        else
            echo
            echo "Testing Frida Complex JavaScript (${runtime^^} runtime)..."
            existing_complex=$(grep "^$method_name," results/results.csv 2>/dev/null | wc -l)
            start_iter=$((existing_complex + 1))
            
            for i in $(seq $start_iter 10); do
                echo -ne "\r  Frida Complex ${runtime^^}: $i/10"
                output=$(frida -l frida_complex.js -f ./build/benchmark --runtime=$runtime 2>&1 | tail -n +2)
                frida_exit_code=${PIPESTATUS[0]}
                if [ $frida_exit_code -gt 0 ]; then
                    echo
                    echo "Frida Complex $runtime failed with exit code $frida_exit_code"
                    exit 1
                fi
                
                if [ ! -z "$output" ]; then
                    complex=$(echo "$output" | grep "Complex ops:" | awk '{print $3}')
                    memory=$(echo "$output" | grep "Max memory:" | awk '{print $3}')
                    
                    if [[ "$complex" =~ ^[0-9]+$ && "$memory" =~ ^[0-9]+$ ]]; then
                        echo "frida_complex_${runtime},complex_ops,$complex" >> results/results.csv
                        echo "frida_complex_${runtime},$memory" >> results/memory.csv
                    else
                        echo "  Warning: Incomplete data for run $i (complex=$complex, memory=$memory)"
                    fi
                fi
            done
            echo
        fi
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
else
    python3 plot.py
fi

echo "Done! See results/performance.png"