import os

INPUT_FILES = [
    "monday_record_sorted.dat",
    "tuesday_record_sorted.dat",
    "wednesday_record_sorted.dat",
    "thursday_record_sorted.dat",
    "friday_record_sorted.dat",
]

def get_key(rec):
    return rec[0:8]

def get_value(rec):
    # strip line ending first, then slice
    rec = rec.rstrip(b"\r\n")
    return float(rec[9:14])

BASE_PATH = r"C:\Users\pgatcomb\Desktop\MainFrameStudies"
OUTPUT_FILE = os.path.join(BASE_PATH, "weekly_total_hours.dat")

readers = [open(os.path.join(BASE_PATH, f), "rb") for f in INPUT_FILES]

# Prime each reader with one line
records = [r.readline() or None for r in readers]

with open(OUTPUT_FILE, "wb") as out:
    while any(records):
        current_id = min(
            rec[0:8] for rec in records if rec is not None
        )

        total = 0.0

        for i, rec in enumerate(records):
            if rec is not None and get_key(rec) == current_id:
                total += get_value(rec)
                records[i] = readers[i].readline() or None

        out.write(b"%s %05.2f\r\n" % (current_id, total))

for r in readers:
    r.close()