import struct
import os
SHIFT_FMT = "<I Q Q I B B I H"
SHIFT_SIZE = 32
INPUT_FILES = [
    "shift_record_monday.dat",
    "shift_record_tuesday.dat",
    "shift_record_wednesday.dat",
    "shift_record_thursday.dat",
    "shift_record_friday.dat"
]

BASE_PATH = r"C:\Users\pgatcomb\Desktop\MainFrameStudies"
OUTPUT_FILE = os.path.join(BASE_PATH, "weekly_total_hours.dat")

readers = [open(os.path.join(BASE_PATH, f), "rb") for f in INPUT_FILES]

def read_shift(f):
    data = f.read(SHIFT_SIZE)
    if not data:
        return None
    return struct.unpack(SHIFT_FMT, data)

records = [read_shift(r) for r in readers]
with open(OUTPUT_FILE, "wb") as out:
    while any(rec is not None for rec in records):

        current_emp = min(
            rec[0] for rec in records if rec is not None
        )

        weekly_total = 0
        weekly_anomaly = 0
        days_present = 0

        for i, rec in enumerate(records):
            if rec is not None and rec[0] == current_emp:
                _, _, _, duration_h, anomaly, _, _, _ = rec
                weekly_total += duration_h
                weekly_anomaly |= anomaly
                days_present += 1
                records[i] = read_shift(readers[i])

        # write weekly record (binary)
        out.write(struct.pack(
            "<I I B B H I",   # example layout
            current_emp,
            weekly_total,
            weekly_anomaly,
            days_present,
            0,
            0
        ))
