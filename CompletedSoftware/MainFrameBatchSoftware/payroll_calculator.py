# Payroll calculator
# Combines employee id with actual hours and off we go
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
``
| Record Name | EmployeeRecord |                 |        |               |
| ----------- | -------------- | --------------- | ------ | ------------- |
| Record Size | 32             |                 |        |               |
|             |                |                 |        |               |
| Offset      | Size           | Field           | Type   | Notes         |
| 0           | 4              | employee_id     | uint32 |               |
| 4           | 1              | department_id   | uint8  |               |
| 5           | 2              | status_flags    | uint16 |               |
| 7           | 4              | pay_rate_cents  | uint32 |               |
| 11          | 1              | pay_type        | uint8  | salary/hourly | # 0 = salary, 1 = hourly
| 12          | 1              | tax_bracket     | uint8  | percent * 100 |
| 13          | 1              | exempt_flags    | uint8  |               |
| 14          | 8              | hire_date_epoch | uint64 |               |
| 22          | 8              | term_date_epoch | uint64 |               |
| 30          | 2              | padding         | uint16 |               |
'''
import struct
import os
HOUR_RECORD_FORMAT = "<I I B B H I"
HOUR_RECORD_SIZE = struct.calcsize(HOUR_RECORD_FORMAT)
assert HOUR_RECORD_SIZE == 16
EMPLOYEE_RECORD_FORMAT = "< I B H I B B B Q Q H"
EMPLOYEE_RECORD_SIZE = struct.calcsize(EMPLOYEE_RECORD_FORMAT)
PAYROLL_RECORD_FORMAT = "< I B B H I I Q Q"
PAYROLL_RECORD_SIZE = struct.calcsize(PAYROLL_RECORD_FORMAT)
assert PAYROLL_RECORD_SIZE == 32
assert EMPLOYEE_RECORD_SIZE == 32
BASE_PATH = r"C:\Users\pgatcomb\Desktop\MainFrameStudies"
HOUR_INPUT_FILE = os.path.join(BASE_PATH, "weekly_total_hours.dat")
EMPLOYEE_INPUT_FILE = os.path.join(BASE_PATH, "employee_master_record.dat")
OUTPUT_FILE = os.path.join(BASE_PATH, "weekly_payroll.dat")
TAX_SCALE = 100

record_count = 0
weekly_index = 0
employee_index = 0


def compute_payroll(hours_from_file, pay_rate_cents, pay_type, tax_rate, exempt_flags):
    hours_regular_hund = 0
    hours_overtime_hund = 0
    # Determine if employee is salary or hourly. If hourly, calculate overtime hours if relevant
    if pay_type == 0:
        hours_regular_hund = 4000
        hours_overtime_hund = 0
    else:
        if hours_from_file > 4000:
            hours_regular_hund = 4000
            hours_overtime_hund = hours_from_file - hours_regular_hund
        else:
            hours_regular_hund = hours_from_file
            hours_overtime_hund = 0

    pay_rate_cents_regular = pay_rate_cents
    gross_regular_cents = (pay_rate_cents_regular * hours_regular_hund) // 100
    gross_overtime_cents = (hours_overtime_hund * pay_rate_cents * 3) // 200
    gross_pay_cents = gross_overtime_cents + gross_regular_cents
    deductions = (gross_pay_cents * tax_rate) // TAX_SCALE
    net_pay = gross_pay_cents - deductions
    return hours_regular_hund, hours_overtime_hund, gross_regular_cents, gross_overtime_cents, gross_pay_cents, deductions, net_pay

total_regular_hours_worked = 0
total_overtime_hours_worked = 0
total_regular_gross = 0
total_overtime_gross = 0
total_deductions = 0
total_net_pay = 0

with open(HOUR_INPUT_FILE, "rb") as hour_file, open(EMPLOYEE_INPUT_FILE, "rb") as employee_file, open(OUTPUT_FILE, "wb") as payroll:
    record_emp = employee_file.read(EMPLOYEE_RECORD_SIZE)
    record_hour = hour_file.read(HOUR_RECORD_SIZE)

    while record_emp or record_hour:
        record_count += 1
        if record_emp:
            m_emp_id, m_dept, m_status, m_pay_rate_cents, m_pay_type, m_tax_rate, m_exempt_flags, _, _, _ = \
                struct.unpack(EMPLOYEE_RECORD_FORMAT, record_emp)
        else:
            m_emp_id = None

        if record_hour:
            emp_id, total_hund, anomaly, days, _, _ = \
                struct.unpack(HOUR_RECORD_FORMAT, record_hour)
        else:
            emp_id = None

        # --- CASE 1: employee with hours ---
        if m_emp_id is not None and emp_id is not None and m_emp_id == emp_id:
            # compute payroll using total_hund
            hours_regular_hund, hours_overtime_hund, gross_regular_cents, gross_overtime_cents, gross_pay_cents, deductions, net_pay = compute_payroll(total_hund, m_pay_rate_cents, m_pay_type, m_tax_rate, m_exempt_flags)
            #print(emp_id, hours_regular_hund, hours_overtime_hund, gross_pay_cents, deductions, net_pay)
            total_regular_hours_worked += (hours_regular_hund/100)
            total_overtime_hours_worked += (hours_overtime_hund/100)
            total_regular_gross += (gross_regular_cents/100)
            total_overtime_gross += (gross_overtime_cents/100)
            total_deductions += (deductions/100)
            total_net_pay += (net_pay/100)
            payroll.write(struct.pack(PAYROLL_RECORD_FORMAT,emp_id, m_dept, m_pay_type, 0, hours_regular_hund, hours_overtime_hund, gross_pay_cents, deductions))
            record_emp = employee_file.read(EMPLOYEE_RECORD_SIZE)
            record_hour = hour_file.read(HOUR_RECORD_SIZE)

        # --- CASE 2: employee with NO hours ---
        elif m_emp_id is not None and (emp_id is None or m_emp_id < emp_id):
            # zero-pay payroll record
            payroll.write(struct.pack(PAYROLL_RECORD_FORMAT,emp_id, m_dept, m_pay_type, 0, 0, 0, 0, 0))
            record_emp = employee_file.read(EMPLOYEE_RECORD_SIZE)

        # --- CASE 3: hours with NO employee ---
        elif emp_id is not None and (m_emp_id is None or m_emp_id > emp_id):
            # anomaly: orphan hours
            record_hour = hour_file.read(HOUR_RECORD_SIZE)


        

print(f"Processed {record_count} weekly records.")
print("-"*20)
print("FINAL REPORT")
print("-"*20)
print("Hours Worked Regular | OT Hours Worked | Regular Gross | OT Gross | Deductions | Net Pay")
print(f"{total_regular_hours_worked:,.2f} {total_overtime_hours_worked:,.2f} ${total_regular_gross:,.2f} ${total_overtime_gross:,.2f} ${total_deductions:,.2f} ${total_net_pay:,.2f}")
