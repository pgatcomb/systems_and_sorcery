'''PDP-8 Assembler'''
'''Writes files into the format memory address, value in a simple txt'''
import sys

COMMENT_MARKER = "/"
operations = {}

# Load in a file consisting of all operations and their base addresses
def populate_operations(file_name):
    with open(file_name, "r") as file:
        for line in file:
            split_line = line.split(",")
            left_side = split_line[0].strip()
            right_side = split_line[1].strip()
            operations[left_side] = int(right_side, 8)

def read_file(file_name:str) -> dict:
    assembled_program = {}
    with open(file_name, "r") as file:
        # Copy the contents of the file into a list so we can do our two pass
        program = list(file)
        symbols = {}  # Variables and their locations
        mem_location = 0o0
        line_counter = 0
        # First pass, identify all symbols, their values and their position, delete comments
        for line in program:
            cleaned_line = line.split("/")[0]   # Ignore all comments
            if cleaned_line == "":   # If our line is now blank, move on
                continue
            if cleaned_line[0] == "*":  # Check this line for a memory mover
                mem_location = int(cleaned_line.replace('*', '') , 8)  # Treat our incoming value as octal
                line_counter = 0
                #print(f"Moved to memory location: {mem_location:o}")
                continue
            if "," in cleaned_line:  # This means we have symbol present
                split_line = cleaned_line.split(",")
                symbol_name = split_line[0].strip()
                effective_address = mem_location + line_counter
                symbols[symbol_name] = effective_address
                #print(f"Symbol {symbol_name} was assigned to mem location {effective_address:o}")
            line_counter += 1
        # Confirm that our values are correct
        print("Mapped symbols and address\n-------------")
        for item, memaddress in symbols.items():
            print(f"Symbol: {item} Address: 0o{memaddress:o}")

        # Progra counter
        pc = 0
        for line in program:
            cleaned_line = line.split("/")[0].strip()
            if not cleaned_line:
                continue
            if "$$" in cleaned_line:
                break
            # Setting a specific memory offset
            if cleaned_line.startswith("*"):
                pc = int(cleaned_line.replace('*', ''), 8) # 12-bit!
                continue
            # Are we dealing with a label?
            if "," in cleaned_line:
                left_side, right_side = map(str.strip, cleaned_line.split(","))
            else:
                left_side, right_side = None, cleaned_line

            # Are we dealing in data or an OPR?
            if "," in cleaned_line and right_side.isdigit():
                assembled_program[pc] = int(right_side, 8) & 0o7777
                pc += 1
                continue

            # OPR or single instruction?
            tokens = right_side.split()

            # Operations, potentially several grouped together
            if all(token in operations for token in tokens):
                word = 0o7000
                for token in tokens:
                    word |= operations[token]
                assembled_program[pc] = word
                pc += 1
                continue

            # MEMORY instruction
            opcode = tokens[0]
            operand = tokens[1] if len(tokens) > 1 else None

            word = operations.get(opcode, 0)

            if operand:
                indirect = operand.startswith("*")
                operand = operand.lstrip("*")

                if operand in symbols:
                    addr = symbols[operand]
                else:
                    addr = int(operand, 8)
                # Indirect or direct pagaing
                if (addr & 0o7600) == (pc & 0o7600):
                    word |= 0o0200  # set page bit
                word |= addr & 0o177

                if indirect:
                    word |= 0o0400

            assembled_program[pc] = word
            pc += 1
    return assembled_program

                    
            
# Write the final program to a txt file for our other program
def write_assembled_program(program_dictionary:dict):
    with open("assembledprogram.txt", "w") as file:
        for item, line in program_dictionary.items():
            file.write(f"0o{item:04o},0o{line:04o}\n")
            
    
# Run the main progarm
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rusty_assembler.py <filename>")
        sys.exit(1)

    input_filename = sys.argv[1]
    populate_operations("pdp8opcodes.txt")
    print("Confirming Operations Hashmap")
    for operation in operations:
        print(f"OPCODE: {operation} BASE VALUE: 0o{operations[operation]:04o}")
    assembled_program = read_file(input_filename)
    sorted_by_key = dict(sorted(assembled_program.items()))
    write_assembled_program(sorted_by_key)
