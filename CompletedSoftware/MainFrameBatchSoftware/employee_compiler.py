import os
import random

BASE_PATH = r"C:\Users\pgatcomb\Desktop\MainFrameStudies"
WEEK_FILE = os.path.join(BASE_PATH, "week.dat")
EMP_MASTER_FILE = os.path.join(BASE_PATH, "employee_master.dat")

random.seed(64)

TAX_CODES = [b'01', b'02', b'03', b'04']
EMP_TYPES = [b'H', b'S']   # Hourly, Salary
PADDING = b' ' * 5

with open(WEEK_FILE, "rb") as week, open(EMP_MASTER_FILE, "wb") as emp:
    for line in week:
        # week.dat format: b'00000056 37.50\r\n'
        emp_id = line[0:8]

        emp_type = random.choice(EMP_TYPES)
        tax_code = random.choice(TAX_CODES)

        record = (
            emp_id +
            emp_type +
            tax_code +
            PADDING
        )

        if len(record) != 16:
            raise RuntimeError("Record length violation")

        emp.write(record)