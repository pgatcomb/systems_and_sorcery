/* 
Version 1.0 PRODUCTION READY
Employee record creator.  This tool generates an imaginary employee record, randomizing various details as it goes.  See the struct below for sturcture
*/

#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>
#include <time.h>

#define START_WEEK_EPOCH 1767589200     // This is january 5 (monday) of 2026 at 0 o'clock and it provides a baseline for hire date
#define TOTAL_EMPLOYEES 0xFFFFFF        // 16 million, this is how many 'employees' we are working with
#define FILENAME "employee_master_record.dat"
#define PAYMAX 125000                 //Maximum pay (per year)
#define PAYMIN 50000                  //Minimum pay (per year)
#define HOURS_PER_YEAR 2080           //How many hours a person works a year
#define SECONDS_IN_YEAR 31536000      //Number of seconds in one year

uint32_t records_saved = 0;

struct EmployeeRecord   // In-memory layout is irrelevant; serialized format is exactly 32 bytes.
{
    uint32_t employee_id;       //Employee ID
    uint8_t department_id;      //Employee's department code
    uint16_t status_flags;      //Any special status flags
    uint32_t pay_rate_cents;    //Employee rate per hour IN CENTS
    uint8_t pay_type;           //0 = hourly, 1 = salary
    uint8_t tax_bracket;        //Tax bracket code
    uint8_t exempt_flags;       //Tax exemption flags
    uint64_t hire_date_epoch;   //Hire date in epoch
    uint64_t term_date_epoch;   //Firing date in epoch
    uint16_t reserved;          //Padidng to get to 32 bytes
};

//Helpers for writing later
static inline void write_u16_le(uint8_t *buf, uint16_t v)
{
    buf[0] = (uint8_t)(v);
    buf[1] = (uint8_t)(v >> 8);
}

static inline void write_u32_le(uint8_t *buf, uint32_t v)
{
    buf[0] = (uint8_t)(v);
    buf[1] = (uint8_t)(v >> 8);
    buf[2] = (uint8_t)(v >> 16);
    buf[3] = (uint8_t)(v >> 24);
}

static inline void write_u64_le(uint8_t *buf, uint64_t v)
{
    buf[0] = (uint8_t)(v);
    buf[1] = (uint8_t)(v >> 8);
    buf[2] = (uint8_t)(v >> 16);
    buf[3] = (uint8_t)(v >> 24);
    buf[4] = (uint8_t)(v >> 32);
    buf[5] = (uint8_t)(v >> 40);
    buf[6] = (uint8_t)(v >> 48);
    buf[7] = (uint8_t)(v >> 56);
}

static inline void emit_record(FILE *fptr, const struct EmployeeRecord *rec)
{
    uint8_t buffer[32];

    write_u32_le(buffer + 0, rec->employee_id);
    buffer[4] = rec->department_id;
    write_u16_le(buffer + 5, rec->status_flags);
    write_u32_le(buffer + 7, rec->pay_rate_cents);
    buffer[11] = rec->pay_type;
    buffer[12] = rec->tax_bracket;
    buffer[13] = rec->exempt_flags;
    write_u64_le(buffer + 14, rec->hire_date_epoch);
    write_u64_le(buffer + 22, rec->term_date_epoch);
    write_u16_le(buffer + 30, rec->reserved);

    if (fwrite(buffer, 32, 1, fptr) != 1) {
        perror("fwrite failed");
        exit(1);
    }
    records_saved++;
}

static struct EmployeeRecord createEmployeeRecord(uint32_t employee_id)
{
    struct EmployeeRecord r1; 
    r1.employee_id=employee_id;
    r1.department_id = rand() % 255;
    r1.status_flags = 0;
    /*
    uint32_t pay_for_year = (rand() % (125000 - 55000 + 1)) + 55000;
    r1.pay_rate_cents = (rand() % (PAYMAX - PAYMIN + 1)) + PAYMIN; //Get yearly number
    r1.pay_rate_cents = r1.pay_rate_cents / (HOURS_PER_YEAR / 100); //Get the hourly number IN CENTS
    */
    uint32_t pay_for_year = (rand() % (PAYMAX - PAYMIN + 1)) + PAYMIN;
    r1.pay_rate_cents = (pay_for_year * 100) / HOURS_PER_YEAR;
    r1.pay_type = rand() % 2;  // Type can either be 0 = salary, 1 = hourly
    /* Tax brackets 
    0-12,400 = 10%
    12-50400 = 12%
    50401-105700 = 22%
    105701-201775 = 24%
    201776-256,225 = 32%
    256226-640,600 = 35%
    640,601+ = 37%
    */
    if (pay_for_year <= 12400)
    {
        r1.tax_bracket = 10;
    }
    else if(pay_for_year <=50400)
    {
        r1.tax_bracket = 12;
    }
    else if(pay_for_year <= 105700)
    {
        r1.tax_bracket = 22;
    }
    else if (pay_for_year <= 201775)
    {
        r1.tax_bracket = 24;
    }
    else if (pay_for_year <= 256225)
    {
        r1.tax_bracket = 32;
    }
    else if (pay_for_year <=640600)
    {
        r1.tax_bracket = 35;
    }
    else
    {
        r1.tax_bracket = 37;
    }
    // People who choose to pay payroll taxes in april instead of have them withheld
    if(rand() % 5 == 3)
    {
        r1.exempt_flags = 1;
    }
    else
    {
        r1.exempt_flags = 0;
    }
    // Generate the hiring date
    // Average american stays at a job for 3.9 years or 1.231e+8 seconds
    r1.hire_date_epoch = START_WEEK_EPOCH - ((rand() % 3) + 3) * SECONDS_IN_YEAR;
    r1.term_date_epoch = 0;   //No one is going to get fired this week.
    r1.reserved = 0;

    return r1;
}

int main()
{
    srand(time(NULL));
    printf("Writing Employee Records, please stand by...\n");
    struct EmployeeRecord rec;
    /* Smoke test (passes)
    printf("Employee ID: %d\n", rec.employee_id);
    printf("Department ID: %d\n", rec.department_id);
    printf("Status flags: %d\n", rec.status_flags);
    printf("Pay Rate (cents): %d\n", rec.pay_rate_cents);
    printf("Pay Type (0=salary, 1=full time): %d\n", rec.pay_type);
    printf("Tax Bracket (x100): %d\n", rec.tax_bracket);
    printf("Exempt flags: %d\n", rec.exempt_flags);
    printf("Hire Date Epoch: %d\n", rec.hire_date_epoch);
    printf("Termination Date Epoch: %d\n", rec.term_date_epoch);
    */
    FILE* fptr;
    fptr = fopen(FILENAME, "wb");
    // checking if the file is created
    if (fptr == NULL) 
    {
        printf("The file is not opened.\n");
        return -1;
    }
    else
    {
        printf("The file is created Successfully.\n");
    }
    setvbuf(fptr, NULL, _IOFBF, 1 << 20); //1 MB file buffer to make things move faster
    for(uint32_t x=0; x < TOTAL_EMPLOYEES; x++)
    {
        rec = createEmployeeRecord(x);
        emit_record(fptr, &rec);
        if (records_saved % 100000 == 0)
        {
            printf("Wrote record %" PRIu32 "\n", records_saved);
        }
    }

    printf("Wrote %" PRIu32 " records total\n", records_saved);
    fclose(fptr);

    return 0;
}