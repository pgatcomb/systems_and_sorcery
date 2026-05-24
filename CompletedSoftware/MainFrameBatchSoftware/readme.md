# Mainframe Batch Software Suite

This suite represents a complete payroll processing cycle, simulating the ingestion of raw timeclock data through to the generation of final payroll reports. It is designed to demonstrate high-volume data handling and binary file manipulation often found in legacy mainframe batch environments.

## Data Specification

Data is stored in a custom binary format to optimize for speed and disk space. Records are written as continuous 16-byte blocks with **Little Endian** byte ordering.

### Punch Record Structure (16 bytes)
| Offset | Field | Type | Description |
|---|---|---|---|
| 0 | Employee ID | uint32 | Obfuscated/Encoded Employee Identifier |
| 4 | Timestamp | uint64 | Epoch timestamp |
| 12 | Punch Meta | uint8 | Bitmask (Bits 0-3: Code, Bits 4-7: Location/Machine) |
| 13 | Error Code | uint8 | 0 = Normal, 1 = Anomalous (e.g., missed punch-out) |
| 14 | Reserved | uint16 | Padding for 16-byte alignment |

## Software Components

### Data Generation
* **punchrecord.c**: A high-performance C utility that generates millions of fictitious timeclock records. It simulates realistic scenarios including standard shifts, break shifts, overtime, and human error (forgotten punches).
* **employee_record.c**: Generates random employee master records in a custom binary format.
* **fakepunchgenerator.py**: A Python-based alternative for generating punch data.

### Processing & Sorting
* **punch_sorter**: Handles the organization of large, randomly generated punch files using an external sort algorithm.
* **daily_sorter.py**: Organizes employee data by day to prepare for shift merging.
* **shift_merger.py**: Logic to pair "In" and "Out" punches into completed work shifts.
* **week_compiler.py**: Aggregates daily shift data into a weekly binary file, performing final merges for the payroll period.

### Calculation & Reporting
* **payroll_calculator**: Merges processed weekly data with employee master files to calculate gross pay, including overtime and deductions.
* **report_generator.py**: Transforms binary results into human-readable payroll records.
* **final_report.txt**: A sample output demonstrating the final state of the payroll data after a full processing run.

### Utilities & Legacy
* **check_data.py**: A diagnostic tool used to inspect the raw binary data at various stages of the pipeline.
* **employee_compiler.py**: An early version of the utility used to compile baseline employee records.
* **week_compiler_alpha.py**: Early alpha version of the weekly aggregation logic.

## Usage Notes

When using the C-based generators (`punchrecord.c`), ensure you configure the following constants for your specific simulation:
* `START_WEEK_EPOCH`: The Monday start time for the data batch.
* `TOTAL_EMPLOYEES`: Number of unique employee IDs to generate (supports up to 16 million).
* `DAY_OF_WEEK`: The specific day (0-6) for the generated punches.

**Warning:** Since the data is written in Little Endian, specific care must be taken if processing this data on Big Endian mainframe systems without a translation layer.
