# Number of parallel processes
N_PARALLEL=8

#pml_file=/mnt/raid/data/xtal/abismal-benchmarks/results/job_/cxidb_81_finer/zn.pml
#img_name=zn.png
pml_file=/mnt/raid/data/xtal/abismal-benchmarks/results/job_/cxidb_81_finer/met_120.pml
img_name=met_120.png



# Function to process a single directory
pdbs=`ls -tr eff_0_asu_0_epoch_*/refine_001.pdb`
#pdbs=(eff_0_asu_0_epoch_{1..20}/refine_001.pdb)

find_missing() {
    echo "Checking for failed renders..."
    # Find directories with missing or small PNG files
    failed_pdbs=()
    for pdb in ${pdbs[@]}; do
        directory=`dirname $pdb`
        if [ ! -f "$directory/$img_name" ]; then
            echo "Missing: $directory/$img_name"
            failed_pdbs+=("$pdb")
        else
            size=$(stat -f%z "$directory/$img_name" 2>/dev/null || stat -c%s "$directory/$img_name" 2>/dev/null)
            if [ "$size" -lt 100000 ]; then
                echo "Too small: $directory/$img_name ($size bytes)"
                failed_pdbs+=("$pdb")
            fi
        fi
    done
    export failed_pdbs
}


# Function to process a single directory
process_directory() {
    local pdb=$1
    local pml_file=$2
    local directory=`dirname $pdb`
    
    echo "Processing $directory"
    cd $directory
    rm -f $img_name
    
    # Launch pymol in background with minimal window interaction
    pymol $pml_file &
    pymol_pid=$!
    
    # Wait for img_name to appear (check every 0.5 seconds, timeout after 60 seconds)
    timeout=60
    elapsed=0
    while [ ! -f $img_name ] && [ $elapsed -lt $timeout ]; do
        sleep 0.5
        elapsed=$((elapsed + 1))
    done
    
    # If file exists, wait for it to finish writing
    if [ -f $img_name ]; then
        echo "File appeared, waiting for write to complete..."
        prev_size=0
        stable_count=0

        sleep 0.5
        # Wait until file size is stable (unchanged for 2 consecutive checks)
        while [ $stable_count -lt 10 ]; do
            sleep 0.5
            curr_size=$(stat -f%z $img_name 2>/dev/null || stat -c%s $img_name 2>/dev/null)
            
            if [ "$curr_size" = "$prev_size" ]; then
                stable_count=$((stable_count + 1))
            else
                stable_count=0
            fi
            
            prev_size=$curr_size
        done
        
        # Extra safety: wait a bit more and sync
        sleep 0.5
        sync
        
        echo "Successfully created $img_name in $directory (size: $curr_size bytes)"
    else
        echo "Warning: $img_name was not created within timeout period in $directory"
    fi
    
    # Kill pymol
    kill $pymol_pid 2>/dev/null
    wait $pymol_pid 2>/dev/null
    
    cd - > /dev/null
}

# Export function and variables for parallel execution
export -f process_directory
export pml_file

find_missing
while [ "${#failed_pdbs[@]}" -gt 0 ]; do
    # Process directories in parallel using bash
    find_missing
    count=0
    for pdb in ${failed_pdbs[@]}; do
        # Launch process in background
        process_directory "$pdb" "$pml_file" &
        count=$((count + 1))
        
        # When we reach N_PARALLEL jobs, wait for them to complete
        if [ $((count % N_PARALLEL)) -eq 0 ]; then
            wait
        fi
    done

    # Wait for any remaining background jobs to complete
    wait
done


echo "All processing complete"
