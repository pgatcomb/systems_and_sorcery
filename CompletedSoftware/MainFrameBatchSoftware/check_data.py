import struct

FILENAME = "weekly_total_hours.dat"

# Adjust if your weekly record layout differs
DATA_STRUCTURE = "<I I B B H I"
RECORD_BYTES = struct.calcsize(DATA_STRUCTURE)

last_employee_id = None
record_count = 0
errors = 0

with open(FILENAME, "rb") as f:
    while True:
        data = f.read(RECORD_BYTES)
        if not data:
            break

        record_count += 1
        employee_id, total_hund, anomaly, days, _, _ = struct.unpack(DATA_STRUCTURE, data)

        # ---- CHECK 1: Sorted order ----
        if last_employee_id is not None and employee_id <= last_employee_id:
            print(f"ERROR: employee_id order broken at {employee_id}")
            errors += 1

        # ---- CHECK 2: Reasonable totals ----
        if total_hund < 0:
            print(f"ERROR: negative time for employee {employee_id}")
            errors += 1

        # 80 hours * 100 = 8000 hundredths (very generous upper bound)
        if total_hund > 8000:
            print(f"WARNING: unusually large time for employee {employee_id}: {total_hund}")

        # ---- CHECK 3: Days present sanity ----
        if days > 7:
            print(f"ERROR: days_present > 7 for employee {employee_id}")
            errors += 1

        # ---- SAMPLE OUTPUT (first few only) ----
        if record_count <= 10:
            print(
                f"emp={employee_id}, "
                f"hours={total_hund/100:.2f}, "
                f"days={days}, "
                f"anomaly={anomaly}"
            )

        last_employee_id = employee_id

print(f"\nRead {record_count} weekly records.")
print(f"Validation errors: {errors}")