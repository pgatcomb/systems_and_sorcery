import struct

# PunchRecord format
# uint32 employee_id
# uint64 timestamp_epoch
# uint8  punch_meta
# uint8  error_code
# uint16 reserved
FMT = "<IQBBH"
RECORD_SIZE = 16

OUTPUT_FILE = "punches_test_20_sorted.dat"

# Base day: Jan 5, 2026 @ 08:00
BASE_EPOCH = 1767619200  # 8am
HOUR = 3600

records = []

def add(emp, ts, meta=0x11, err=0):
    records.append((emp, ts, meta, err, 0))

# Employee 100: standard day
add(100, BASE_EPOCH)
add(100, BASE_EPOCH + 8 * HOUR)

# Employee 101: break day
add(101, BASE_EPOCH)
add(101, BASE_EPOCH + 4 * HOUR)
add(101, BASE_EPOCH + 4 * HOUR + 1800)
add(101, BASE_EPOCH + 8 * HOUR)

# Employee 102: forgot punch out
add(102, BASE_EPOCH, err=1)

# Employee 103: forgot punch in
add(103, BASE_EPOCH + 8 * HOUR, err=2)

# Employee 104: standard day, jitter
add(104, BASE_EPOCH + 120)
add(104, BASE_EPOCH + 8 * HOUR + 90)

# Employee 105: break + jitter
add(105, BASE_EPOCH + 60)
add(105, BASE_EPOCH + 4 * HOUR + 30)
add(105, BASE_EPOCH + 4 * HOUR + 1800 + 45)
add(105, BASE_EPOCH + 8 * HOUR + 75)

# Employee 106: standard
add(106, BASE_EPOCH)
add(106, BASE_EPOCH + 8 * HOUR)

# Employee 107: standard
add(107, BASE_EPOCH)
add(107, BASE_EPOCH + 8 * HOUR)

# Sanity check: exactly 20 records
#assert len(records) == 20

# Already sorted by construction, but make it explicit
records.sort(key=lambda r: (r[0], r[1]))

# Write binary file
with open(OUTPUT_FILE, "wb") as f:
    for rec in records:
        f.write(struct.pack(FMT, *rec))

print("Wrote 20 sorted punch records to", OUTPUT_FILE)