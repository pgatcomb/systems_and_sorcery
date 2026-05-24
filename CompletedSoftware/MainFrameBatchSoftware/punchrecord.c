/*
Punch record maker version 1.01 --PRODUCTION READY--
This is a working program that generates fictious timeclock data
written as contnuous 16-byte blocks in binary files (no newline, don't be that guy who uses .readline()!)
The data is written LITTLE ENDIAN, so watch out if you're using this data on a mainframe.
You're going to be editing the start week, total employees, day of week and filename and running.
*/


#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>
#include <time.h>

// Define key and a mask for our cipher
#define KEY 0x40
#define MASK24 0xFFFFFF
// This is january 5 (monday) of 2026 at 0 o'clock
#define START_WEEK_EPOCH 1767589200
// This is the amount of seconds from midnight a typical work day starts (8 am)
#define WORK_DAY_START_OFFSET 28800
#define TOTAL_EMPLOYEES 0xFFFFFF // 16 million
#define DAY_OF_WEEK 0
#define FILENAME "punches_test.dat"

uint64_t total_punches = 0;

struct PunchRecord
{
    uint32_t employee_id;       //employee id from 0 through 4294967296
    uint64_t timestamp_epoch;   //timestamp large enough to deal with that stupid 2106 bug
    uint8_t punch_meta;         //First four bits are codes, second four bits are location/machine
    uint8_t error_code;         //Right now a 0 = normal, 1 = anomalous (used if 'employee' forgets to punch out)
    uint16_t reserved;          //Leave two bytes empty space to get us to 16-byte total size
};

static uint64_t get_time()
{
    // There are 86400 seconds in a day
    return START_WEEK_EPOCH + (DAY_OF_WEEK * 86400);
}

static uint32_t rotl24(uint32_t x, uint8_t r) 
{
    r &= 23;
    return ((x << r) | (x >> (24 - r))) & MASK24;
}

static uint32_t encode_value(uint32_t value)
{
    uint32_t id = value & MASK24;
    id ^= KEY;
    id = rotl24(id, 2);
    return id;
}

static struct PunchRecord createPunchRecord(uint32_t employee_id, uint64_t time_offset)
{
    struct PunchRecord r1; 
    r1.employee_id=encode_value(employee_id);
    r1.timestamp_epoch=get_time() + time_offset;
    r1.punch_meta=strtol("00010001", NULL, 2);
    r1.error_code=strtol("00000000", NULL, 2);
    r1.reserved=0;
    return r1;
}


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


static inline void emit_punch(FILE *fptr, const struct PunchRecord *rec)
{
    uint8_t buffer[16];
    write_u32_le(buffer + 0,  rec->employee_id);
    write_u64_le(buffer + 4,  rec->timestamp_epoch);
    buffer[12] = rec->punch_meta;
    buffer[13] = rec->error_code;
    write_u16_le(buffer + 14, rec->reserved);
    if (fwrite(buffer, 16, 1, fptr) != 1) {
        perror("fwrite failed");
        exit(1);
    }
    total_punches++;

}

int main()
{
    srand(time(NULL));
    printf("Writing Punch Records, please wait...\n");
    struct PunchRecord rec;
    uint8_t dice;
    uint64_t time_offset;
    uint8_t punch_details;
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
        dice = (rand() % 100) + 1;  //Our dice helps create a scenario for each employee so we can generate some records for them
        punch_details = (rand() % 127);
        if (total_punches % 100000 == 0)
        {
            printf("Wrote punch %" PRIu64 "\n", total_punches);
        }
        if (rand() % 2 == 2)
        {
            punch_details += 127;
        }
        if (dice <= 80) 
        {
            // Standard 8 hour day
            time_offset = WORK_DAY_START_OFFSET + ((rand() % 900) - 450);
            rec = createPunchRecord(x, time_offset);
            rec.punch_meta = punch_details;
            emit_punch(fptr, &rec);
            time_offset = WORK_DAY_START_OFFSET + ((rand() % 900) - 450) + 28800;
            rec = createPunchRecord(x, time_offset);
            rec.punch_meta = punch_details;
            emit_punch(fptr, &rec);
        }
        else if (dice <= 92) {
            // Break shift
            time_offset = WORK_DAY_START_OFFSET + ((rand() % 900) - 450);
            rec = createPunchRecord(x, time_offset);
            rec.punch_meta = punch_details;            
            emit_punch(fptr, &rec);

            time_offset = WORK_DAY_START_OFFSET + ((rand() % 900) - 450) + 14400;
            rec = createPunchRecord(x, time_offset);
            rec.punch_meta = punch_details;
            emit_punch(fptr, &rec);

            time_offset = time_offset + 1800 + ((rand() % 900) - 450); 
            rec = createPunchRecord(x, time_offset);
            rec.punch_meta = punch_details;
            emit_punch(fptr, &rec);

            time_offset = WORK_DAY_START_OFFSET + ((rand() % 900) - 450) + 28800;
            rec = createPunchRecord(x, time_offset);
            rec.punch_meta = punch_details;
            emit_punch(fptr, &rec);
        }
        else if (dice <= 98) {
            // Overtime (up to 3 hours)
            time_offset = WORK_DAY_START_OFFSET + ((rand() % 900) - 450);
            rec = createPunchRecord(x, time_offset);
            rec.punch_meta = punch_details;
            emit_punch(fptr, &rec);


            time_offset = WORK_DAY_START_OFFSET + (rand() % 10800) + 28800;
            rec = createPunchRecord(x, time_offset);
            rec.punch_meta = punch_details;
            emit_punch(fptr, &rec);
        }
        else if (dice <= 99)
        {
            // forgot to punch out!
            time_offset = WORK_DAY_START_OFFSET + ((rand() % 900) - 450);
            rec = createPunchRecord(x, time_offset);
            rec.punch_meta = punch_details;
            rec.error_code = 1;
            emit_punch(fptr, &rec);
        }
        else
        {
            //You didn't come into work that day!
        }
    }
    printf("Wrote %" PRIu64 " punches total\n", total_punches);
    fclose(fptr);
    return 0;
}