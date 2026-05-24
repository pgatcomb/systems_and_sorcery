'''
ShiftMerger
This tool reads in a sorted punch file and calculates the total amount of second
worked that day.  
The format of the punch data is as such:
| Record Name | PunchRecord |                 |        |                    |
| ----------- | ----------- | --------------- | ------ | ------------------ |
| Record Size | 16          |                 |        |                    |
| Offset      | Size        | Field           | Type   | Notes              |
| 0           | 4           | employee_id     | uint32 |                    |
| 4           | 8           | timestamp_epoch | uint64 |                    |
| 12          | 1           | punch_meta      | uint8  | hi=punch,lo=source |
| 13          | 1           | error_code      | uint8  |                    |
| 14          | 2           | reserved        | uint16 |                    |
The format of the shift record data is as such:
| Record Name | ShiftRecord |                    |        |       |
| ----------- | ----------- | ------------------ | ------ | ----- |
| Record Size | 32          |                    |        |       |
| Offset      | Size        | Field              | Type   | Notes |
| 0           | 4           | employee_id        | uint32 |       |
| 4           | 8           | start_epoch        | uint64 |       |
| 12          | 8           | end_epoch          | uint64 |       |
| 20          | 4           | duration_hundreths | uint32 |       |
| 24          | 1           | anomaly_code       | uint8  |       |
| 25          | 1           | shift_seq          | uint8  |       |
| 26          | 4           | pay_period_id      | uint32 |       |
| 30          | 2           | reserved           | uint16 |       |
'''
import struct
import os

INPUT_FILE = "punches_friday_sorted.dat"
OUTPUT_FILE = "shift_record_friday.dat"
INPUT_RECORD_SIZE = 16
INPUT_RECORD_FORMAT = '<IQBBH'
OUTPUT_RECORD_SIZE = 32
OUTPUT_RECORD_FORMAT = "<I Q Q I B B I H"
FILE_PATH = "C:\\Users\\pgatcomb\\Desktop\\MainFrameStudies\\"
SHIFT_SEQ = 0
PAY_PERIOD_ID = 1

records_processed = 0
shift_records_processed = 0

with open(f"{FILE_PATH}{OUTPUT_FILE}", "wb") as f_out, open(f"{FILE_PATH}{INPUT_FILE}", "rb") as reader:
    try:
        current_employee_id = None
        seconds_worked = 0
        punched_in = False
        shift_start = None
        last_timestamp = None
        while True:
            record = reader.read(INPUT_RECORD_SIZE)

            if record:
                records_processed += 1
                emp_id, timestamp, _, _, _ = struct.unpack(INPUT_RECORD_FORMAT, record)

                # --- FIRST RECORD INITIALIZATION ---
                if current_employee_id is None:
                    current_employee_id = emp_id
                    punched_in = True
                    shift_start = timestamp
                    last_timestamp = timestamp
                    continue

                # --- CONTROL BREAK: NEW EMPLOYEE ---
                if emp_id != current_employee_id:
                    # Finalize PREVIOUS employee
                    if punched_in:
                        # Missing punch-out
                        #print(f"{current_employee_id} forgot to punch out")
                        record_bytes = struct.pack(
                            OUTPUT_RECORD_FORMAT,
                            current_employee_id,
                            shift_start,
                            last_timestamp,          # end_epoch
                            0,
                            1,                       # Anomaly code 1 (forgot to punch out)
                            SHIFT_SEQ,
                            PAY_PERIOD_ID,
                            0                        # reserved
                        )
                        f_out.write(record_bytes)
                    else:
                        #print(f"{current_employee_id} worked {seconds_worked} seconds")
                        # Warning: We assume all intervals are positive. This should be checked and hardened against todo
                        duration_hundredths = (abs(seconds_worked) * 100) // 3600
                        record_bytes = struct.pack(
                            OUTPUT_RECORD_FORMAT,
                            current_employee_id,
                            shift_start,
                            last_timestamp,          # end_epoch
                            duration_hundredths,
                            0,
                            SHIFT_SEQ,
                            PAY_PERIOD_ID,
                            0                        # reserved
                        )
                        f_out.write(record_bytes)
                        # anomaly_code = OK

                    shift_records_processed += 1

                    # Reset state for NEW employee
                    current_employee_id = emp_id
                    seconds_worked = 0
                    punched_in = True
                    shift_start = timestamp
                    last_timestamp = timestamp
                    continue

                # --- SAME EMPLOYEE: PROCESS PUNCH ---
                if punched_in:
                    # Punch OUT
                    seconds_worked += (timestamp - last_timestamp)
                    punched_in = False
                else:
                    # Punch IN
                    punched_in = True
                    last_timestamp = timestamp

            else:
                # --- EOF: FINALIZE LAST EMPLOYEE ---
                if current_employee_id is not None:
                    if punched_in:
                        record_bytes = struct.pack(
                            OUTPUT_RECORD_FORMAT,
                            current_employee_id,
                            shift_start,
                            last_timestamp,          # end_epoch
                            0,
                            1,                       # Anomaly code 1 (forgot to punch out)
                            SHIFT_SEQ,
                            PAY_PERIOD_ID,
                            0                        # reserved
                        )
                        f_out.write(record_bytes)
                    else:
                        # Warning: We assume all intervals are positive. This should be checked and hardened against todo
                        duration_hundredths = (abs(seconds_worked) * 100) // 3600
                        record_bytes = struct.pack(
                            OUTPUT_RECORD_FORMAT,
                            current_employee_id,
                            shift_start,
                            last_timestamp,          # end_epoch
                            duration_hundredths,
                            0,
                            SHIFT_SEQ,
                            PAY_PERIOD_ID,
                            0                        # reserved
                        )
                        f_out.write(record_bytes)

                    shift_records_processed += 1
                break
    except:
        print(f"Fatal error on record {records_processed}. {last_timestamp} {timestamp} {seconds_worked}")
                
    finally:
        f_out.close()
        reader.close()

print(f"{records_processed} punches processed into {shift_records_processed} shift records.")