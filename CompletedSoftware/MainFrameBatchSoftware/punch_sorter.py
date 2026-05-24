'''
Punch sort and merge program. NON PRODUCTION VERSION 0.9
This program takes in a master punch file consisting of punches of this description:

Offset	Size	Field	Type
0	4	employee_id	uint32
4	8	timestamp_epoch	uint64
12	1	punch_meta	uint8
13	1	error_code	uint8
14	2	reserved	uint16

It then sorts the punches by employee_id then by timestamp_epoch and writes a file that contains
the original data all neatly sorted.
'''
import struct
import os

INPUT_FILE = "punches_friday.dat"
#OUTPUT_FILE = "punches_test_sorted.dat"
OUTPUT_FILE = "punches_friday_sorted.dat"
RECORD_SIZE = 16
CHUNK_LIMIT = 5_000_000   # About 75 Mb
RECORD_FORMAT = '<IQBBH'  # All fields stored little-endian to preserve lexicographic sort order

chunk_count = 0
chunk_files = []
output_path = "C:\\Users\\pgatcomb\\Desktop\\MainFrameStudies\\"
"""
Step 1 - Break files neatly into smaller chunks to sort individually
"""


with open(f"{output_path}{INPUT_FILE}", "rb", buffering=65536) as file:
    while True:
        print(f"Writing Chunk# {chunk_count}")
        data = [] # Re initialize data list
        for x in range(CHUNK_LIMIT):
            record = file.read(RECORD_SIZE)
            if not record:  # EOF reached 'early'
                break

            emp_id, ts, meta, err, res = struct.unpack(RECORD_FORMAT, record)
            data.append((emp_id, ts, record))

        if not data:   # EOF All records reached
            break

        data.sort(key=lambda r: (r[0], r[1]))

        filename = f"{output_path}chunk_{chunk_count}.bin"
        with open(filename, "wb", buffering=65536) as chunk_f:
            for _, _, raw in data:
                chunk_f.write(raw)

        
        chunk_files.append(filename)
        chunk_count += 1

print(f"{chunk_count} Chunk Files Written and sorted")

"""
STEP 2: Take the files in and k-way sort them by employee_id
"""


readers = []
records_processed = 0
with open(f"{output_path}{OUTPUT_FILE}", "wb", buffering=65536) as f_out:

    try:
        for chunk_file in chunk_files:
            readers.append(open(f"{chunk_file}","rb", buffering=65536))
        
        current_records = []
        for r in readers:
            raw = r.read(RECORD_SIZE)
            if raw:
                data = struct.unpack(RECORD_FORMAT, raw)
                current_records.append((data[0], raw))
            else:
                current_records.append(None)


        while any(rec is not None for rec in current_records):
            smallest_index = -1

            for i, rec in enumerate(current_records):
                if rec is None:
                    continue
                if smallest_index == -1 or rec[:2] < current_records[smallest_index][:2]:
                    smallest_index = i

            f_out.write(current_records[smallest_index][1])
            records_processed += 1
            #if records_processed % 1000000 == 0:
                #print(f"{records_processed} records processed.")

            next_rec = readers[smallest_index].read(RECORD_SIZE)
            if next_rec:
                data = struct.unpack(RECORD_FORMAT, next_rec)
                current_records[smallest_index] = (data[0], next_rec)       
            else:
                current_records[smallest_index] = None
            

    finally:
        for r in readers:
            r.close()
        f_out.close()

print(f"{records_processed} records processed.")

for i in range(chunk_count):
    filename = f"chunk_{i}.bin"
    if os.path.exists(filename):
        os.remove(filename)