'''
This program takes in employee IDs and times and sorts them by employee ID
The data is stored in a 16-byte line like:
00001216 09.75\r\n
Since the timecard data file is too large, the program breaks the incoming data into smaller files, sorts those and then
merges them into a master file
WARNING OF DEATH: This program is now BROKEN due to switching to a 16-bit continuous data
'''

import os

# ============================
# STEP #1 - BREAK FILES INTO CHUNKS
# ============================

INPUT_FILE = "friday.dat"
OUTPUT_FILE = "friday_sorted.dat"
RECORD_SIZE = 16
CHUNK_LIMIT = 25000 # This will be closer to 30 million later, but we've got time :)
chunk_count = 0
chunk_files = [] #figure out the names of each chunked file
output_path = "C:\\Users\\pgatcomb\\Desktop\\MainFrameStudies\\"
with open(f"{output_path}{INPUT_FILE}", "rb") as file:
    while True:
        data = [] # Re initialize data list
        for x in range(CHUNK_LIMIT):
            record = file.readline()#(RECORD_SIZE)
            if not record:  # EOF reached 'early'
                break
            data.append(record)

        if not data:   # EOF All records reached
            break

        data.sort()

        filename = f"chunk_{chunk_count}.bin"
        with open(filename, "wb") as chunk_f:
            for record in data:
                chunk_f.write(record)
        
        chunk_files.append(filename)
        chunk_count += 1


# ============================
# STEP #2 - MERGE INTO FILE
# ============================

def get_key(raw_bytes):
    return raw_bytes[0:8]

readers = []
with open(f"{output_path}{OUTPUT_FILE}", "wb") as f_out:

    try:
        for chunk_file in chunk_files:
            readers.append(open(f"{output_path}{chunk_file}","rb"))
        
        current_records = []
        for r in readers:
            raw = r.readline()#(RECORD_SIZE)
            if raw:
                current_records.append((get_key(raw), raw))
            else:
                current_records.append(None)

        while any(rec is not None for rec in current_records):
            smallest_index = -1

            for i, rec in enumerate(current_records):
                if rec is None:
                    continue
                if smallest_index == -1 or rec[0] < current_records[smallest_index][0]:
                    smallest_index = i

            f_out.write(current_records[smallest_index][1])

            next_rec = readers[smallest_index].readline()#(RECORD_SIZE)
            if next_rec:
                current_records[smallest_index] = (get_key(next_rec), next_rec)        
            else:
                current_records[smallest_index] = None
    finally:
        for r in readers:
            r.close()
        f_out.close()

for i in range(chunk_count):
    filename = f"chunk_{i}.bin"
    if os.path.exists(filename):
        os.remove(filename)
        print(f"Deleted {filename}")