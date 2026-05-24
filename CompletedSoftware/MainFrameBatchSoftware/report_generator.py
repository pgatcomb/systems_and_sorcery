# Report Generator
'''
Offset  Size  Field
--------------------------------
0       4     employee_id
4       1     department_id
5       1     pay_type           (optional, but useful)
6       2     payroll_flags
8       4     hours_regular_hund
12      4     hours_overtime_hund
16      8     gross_pay_cents
24      8     deductions_cents
--------------------------------
Total: 32 bytes
'''
import os
import struct
PAYROLL_RECORD_FORMAT = "< I B B H I I Q Q"
PAYROLL_RECORD_SIZE = struct.calcsize(PAYROLL_RECORD_FORMAT)
assert PAYROLL_RECORD_SIZE == 32
BASE_PATH = r"C:\Users\pgatcomb\Desktop\MainFrameStudies"
INPUT_FILE = os.path.join(BASE_PATH, "weekly_payroll.dat")
OUTPUT_FILE = os.path.join(BASE_PATH, "final_report.txt")
NUMBER_DEPARTMENTS = 255
run_date = "4/22/2026"

# Initialize accumlator arrays
reg_hours = []
ot_hours = []
gross_pay = []
pay_deductions = []
for x in range(NUMBER_DEPARTMENTS):
    reg_hours.append(0)
    ot_hours.append(0)
    gross_pay.append(0)
    pay_deductions.append(0)

records_processed = 0
with open(INPUT_FILE, "rb") as payroll:
    while True:
        record = payroll.read(PAYROLL_RECORD_SIZE)
        if record:
            emp_id, dept, pay_type, _, hours_regular_hund, hours_overtime_hund, gross_pay_cents, deductions = struct.unpack(PAYROLL_RECORD_FORMAT, record)
            reg_hours[dept] += hours_regular_hund
            ot_hours[dept] += hours_overtime_hund
            gross_pay[dept] += gross_pay_cents
            pay_deductions[dept] += deductions
        else:
            print("Printing report...")
            break

# Smoke test, works fine!
'''
print("Department | Regular Hours | Ot Hours | Gross Pay | Deductions | Net Pay")
for department in range(NUMBER_DEPARTMENTS + 1):
    net_pay = gross_pay[department] - pay_deductions[department]
    print(f"{department} {reg_hours[department]/100:,.2f} {ot_hours[department]/100:,.2f} ${gross_pay[department]/100:,.2f} ${pay_deductions[department]/100:,.2f} ${net_pay/100:,.2f}")
'''

def fmt_int(val, width):
    return f"{val:>{width}d}"

def fmt_hours(val_hund, width):
    return f"{val_hund/100:>{width},.2f}"

def fmt_money(val_cents, width):
    return f"{val_cents/100:>{width-1},.2f}"

line_width = 97
with open(OUTPUT_FILE, "w") as out:

    out.write("*" * line_width + "\n")
    out.write("FINAL PAYROLL REPORT".center(line_width) + "\n")
    out.write(f"RUN DATE: {run_date}".ljust(line_width) + "\n")
    out.write("*" * line_width + "\n")
    out.write(
    f"{'Department':>10}"
    f"{'Regular Hours':>18}"
    f"{'OT Hours':>15}"
    f"{'Gross Pay':>18}"
    f"{'Deductions':>18}"
    f"{'Net Pay':>18}\n")
    out.write("-" * line_width + "\n")
    for department in range(NUMBER_DEPARTMENTS):    
        net_pay = gross_pay[department] - pay_deductions[department]
        out.write(
        f"{department:>10}"
        f"{fmt_hours(reg_hours[department], 18)}"
        f"{fmt_hours(ot_hours[department], 15)}"
        f"{fmt_money(gross_pay[department], 18)}"
        f"{fmt_money(pay_deductions[department], 18)}"
        f"{fmt_money(net_pay, 18)}\n")
    
