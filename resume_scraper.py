#!/usr/bin/env python3
"""
Resume scraper - continue processing from where it left off
"""

import os
import sys
import csv
import glob
from parallel_scraper import process_chunk_file, combine_processed_chunks

def check_progress():
    """Check what chunks have been processed and what's remaining"""
    chunks_dir = "chunks"
    processed_dir = "processed_chunks"
    
    if not os.path.exists(chunks_dir):
        print("No chunks directory found. Run parallel_scraper.py first.")
        return
    
    # Get all chunk files
    chunk_files = sorted(glob.glob(os.path.join(chunks_dir, "chunk_*.csv")))
    
    # Get all processed chunk files
    processed_files = glob.glob(os.path.join(processed_dir, "*_processed.csv"))
    processed_chunk_ids = set()
    
    for pf in processed_files:
        chunk_id = os.path.basename(pf).split('_processed')[0]
        processed_chunk_ids.add(chunk_id)
    
    # Find remaining chunks
    remaining_chunks = []
    for chunk_file in chunk_files:
        chunk_id = os.path.basename(chunk_file).split('.')[0]
        if chunk_id not in processed_chunk_ids:
            remaining_chunks.append(chunk_file)
    
    print(f"Total chunks: {len(chunk_files)}")
    print(f"Processed chunks: {len(processed_files)}")
    print(f"Remaining chunks: {len(remaining_chunks)}")
    
    return remaining_chunks

def resume_processing(remaining_chunks, max_workers=4):
    """Resume processing of remaining chunks"""
    from concurrent.futures import ProcessPoolExecutor, as_completed
    
    print(f"Resuming processing of {len(remaining_chunks)} chunks...")
    
    processed_chunks = []
    
    # Use ProcessPoolExecutor for chunk processing
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_chunk = {executor.submit(process_chunk_file, chunk): chunk for chunk in remaining_chunks}
        
        for future in as_completed(future_to_chunk):
            processed_chunk = future.result()
            processed_chunks.append(processed_chunk)
            print(f"Completed processing chunk: {processed_chunk}")
    
    return processed_chunks

def main():
    print("Checking processing progress...")
    
    # Check what's been processed
    remaining_chunks = check_progress()
    
    if not remaining_chunks:
        print("All chunks have been processed!")
        
        # Check if final output exists
        if os.path.exists("UpdatedTestLinks.csv"):
            print("Final output file already exists: UpdatedTestLinks.csv")
        else:
            print("Creating final output file...")
            # Get all processed chunks
            processed_files = sorted(glob.glob("processed_chunks/*_processed.csv"))
            combine_processed_chunks(processed_files, "UpdatedTestLinks.csv")
        
        return
    
    # Resume processing
    print(f"\nResuming processing of {len(remaining_chunks)} remaining chunks...")
    processed_chunks = resume_processing(remaining_chunks)
    
    # Combine all processed chunks
    print("\nCombining all processed chunks...")
    all_processed_files = sorted(glob.glob("processed_chunks/*_processed.csv"))
    combine_processed_chunks(all_processed_files, "UpdatedTestLinks.csv")
    
    print("Resume processing complete!")

if __name__ == "__main__":
    main()
