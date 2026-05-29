/* 
Rust PDP-8 Emulator
Opcodes on a pdp-8 consist of:
0 (000) - Logical AND
1 (001) - TAD (Two's compliment add)
2 (002) - ISZ Increment and skip if zero
3 (003) - DCA Deposit/Clear Accumulator
4 (011) - JMS Jump to subroutine
5 (101) - JMP Jump
6 (110) - IOT (IO transfer)
7 (111) - OPR Operate / Microcode ops
If bit is 0, it's group 1
    7 = CLA (clear AC)
    6 - CLL (Clear link)
    5 - CMA (Complement AC)
    4 - Compliment Link
    3 - Increment AC
    2 - RAR Rotate AC + Link Right
    1 - RAL - Rotate AC + Link left

e.g. 1110 1100 0001 = octal 7201 (CLA CLL IAC)
If bit is 1
    7 - SMA - Skip if AC < 0
    6 - SZA - Skip if AC == 0
    5 - SNL - Skip if link == 1
    4 - CLA - Clear AC
    3 - OSR - OR AC with switch register
    2 - HLT - Halt
Addressing modes
    8 - Indirect (1 = direct)
    7 - Zero page (0) or current page (1)
    0-6 - 7-bit Offset
*/
use std::fs::File;
use std::io::{BufRead, BufReader, self, Write, Read};
use std::env;

const BIT_MASK_12: u16 = 0o7777;

/// CPU implementation consists of memory, program counter, accumulator and link bit. We're dealing in a base model pdp-8 without any of the
/// Fancy math modelling in it, or the extended memory
struct Cpu {
    mem: [u16; 4096], // Memory is 2 ^ 12
    pc: u16,
    ac: u16,
    link: bool,
    running: bool,
}

impl Cpu {
    /// Create a new, blank CPU
    fn new() -> Self {
        Self {
            mem: [0; 4096],  // 2^12 words
            pc: 0,
            ac: 0,
            link: false,
            running: false,
        }
    }

    // Safe retrieval of value at address in case we refactor later
    fn get_value_at_address(&self, address: u16) -> u16 {
        self.mem[address as usize]
    }

    // Apply value at memory address
    fn set_value_at_address(&mut self, address: u16, value: u16) {
        self.mem[address as usize] = value & BIT_MASK_12;
    }

    /// Simulate the fetch and process cycle of our computer
    fn do_cycle(&mut self) -> bool {
        if !self.running {
            return false;
        }

        // Get current memory item
        let raw_byte = self.get_value_at_address(self.pc);
        
        // Increment PC immediately
        self.pc = (self.pc + 1) & BIT_MASK_12;

        if raw_byte == 0 {
            // If we find an empty word, we just keep going
            return true; 
        }
        // The opcode is equal to the first 3 bits
        let opcode = (raw_byte >> 9) & 0o7;

        // Opcode 7 are all microcodes
        if opcode == 7 {
            self.op_opr(raw_byte);
        } else if opcode == 6 {
            self.op_iot(raw_byte);
        } else {
            let indirect_bit = (raw_byte >> 8) & 0b1;
            let page_bit = (raw_byte >> 7) & 0b1;
            let offset = raw_byte & 0o177;
            
            // Calculate effective address if we need it, we may not if we're on the same pages
            let effective_address = self.calculate_address(offset, indirect_bit, page_bit);
            
            // 6 and 7 are already accounted for
            match opcode {
                0 => self.op_and(effective_address),
                1 => self.op_tad(effective_address),
                2 => self.op_isz(effective_address),
                3 => self.op_dca(effective_address),
                4 => self.op_jms(effective_address),
                5 => self.op_jmp(effective_address),
                _ => unreachable!(),
            }
        }
        // Comment out if not debugging
        println!("Opcode: 0o{:04o} PC: 0o{:04o} AC: 0o{:04o} Link: {}", raw_byte, self.pc, self.ac, self.link);
        
        self.running && self.pc <= 4094   //If our PC exceeds our memory, we're out of index
    }

    // Calculate the effective address, this is based on the page we're on plus it's desired address
    fn calculate_address(&mut self, offset: u16, indirect: u16, page: u16) -> u16 {
        let base_address: u16 = if page == 0 {
            0
        } else {
            (self.pc - 1) & 0o7600 // -1 because we already incremented PC
        };

        let mut address = base_address | offset;

        if indirect == 1 {
            // PDP-8 Auto-indexing feature: Pages 0o0010 through 0o0017 increment before use
            if (0o0010..=0o0017).contains(&address) {
                let incremented = (self.get_value_at_address(address) + 1) & BIT_MASK_12;
                self.set_value_at_address(address, incremented);
            }
            address = self.get_value_at_address(address);
        }
        address
    }

    // & with the value at the address plus the AC
    fn op_and(&mut self, address: u16) {
        self.ac &= self.get_value_at_address(address);
    }

    // Add value to AC, clicking the link if we go over
    fn op_tad(&mut self, address: u16) {
        let value = self.get_value_at_address(address);
        let sum = self.ac as u32 + value as u32;
        let carry = (sum >> 12) & 1;
        
        self.ac = (sum & BIT_MASK_12 as u32) as u16;
        if carry == 1 {
            self.link = !self.link;
        }
    }

    // Increment AC, if we go over, up the program counter by one
    fn op_isz(&mut self, address: u16) {
        let new_val = (self.get_value_at_address(address) + 1) & BIT_MASK_12;
        self.set_value_at_address(address, new_val);
        if new_val == 0 {
            self.pc = (self.pc + 1) & BIT_MASK_12; // Skip next instruction
        }
    }

    // Place value of AC into a specific address
    fn op_dca(&mut self, address: u16) {
        self.set_value_at_address(address, self.ac);
        self.ac = 0;
    }

    // Jump to subroutine and leave our current program counter where we are
    fn op_jms(&mut self, address: u16) {
        self.set_value_at_address(address, self.pc);
        self.pc = (address + 1) & BIT_MASK_12;
    }


    // Jump immediately to a new address
    fn op_jmp(&mut self, address: u16) {
        self.pc = address;
    }

    // Input/output. We're going to handle this in a very basic fashion
    fn op_iot(&mut self, instr: u16) {
        // Step 1, separate the device from what we're doing with it.
        let device = (instr >> 3) & 0o77;
        let func:u16 = instr & 0o7;

        match device {
            // The only device we actually care about is the one that makes letters appear
            0o04 => {
                match func{
                    1 => self.pc = (self.pc + 1) & BIT_MASK_12,   // We're not waiting for the printer to be ready, so just go
                    2 => {},  // Nothing since we have no flags to clear
                    4 => {
                        let character = (self.ac & 0o200) as u8 as char;
                        print!("{}", character);
                        io::stdout().flush().unwrap();
                        },
                    6 => {
                        let character = (self.ac & 0o200) as u8 as char;  // Technically we're also clearing flags here
                        print!("{}", character);
                        io::stdout().flush().unwrap();
                        },
                    _ => {},
                        }
                    },
            0o03 => {
                match func {
                    1 => {}, // Skip if key pressed. Bascially impossible without threading.
                    6 => {
                        let mut buff = [0; 1];      // We'll try to capture exactly one character from the keyboard and pop it in the AC
                        io::stdin().read_exact(&mut buff).unwrap();
                        self.ac = buff[0] as u16;
                    },
                    _ => {},
                }   

            },
            _ => {}
        }

        
    }

    // Microcode handling
    fn op_opr(&mut self, instr: u16) {
        if (instr & 0o0400) == 0 {
            self.exec_group1(instr);
        } else {
            self.exec_group2(instr);
        }
    }

    /// Group 1 microcodes are fairly straightforward and can be combined
    fn exec_group1(&mut self, micro: u16) {
        // Sequence 1
        if micro & 0o0200 != 0 { self.ac = 0; }
        if micro & 0o0100 != 0 { self.link = false; }
        
        // Sequence 2
        if micro & 0o0040 != 0 { self.ac = !self.ac & BIT_MASK_12; }
        if micro & 0o0020 != 0 { self.link = !self.link; }
        
        // Sequence 3
        if micro & 0o0001 != 0 {
            let sum = self.ac as u32 + 1;
            self.ac = (sum & BIT_MASK_12 as u32) as u16;
            if (sum >> 12) & 1 == 1 {
                self.link = !self.link; // IAC behaves like TAD regarding link
            }
        }
        
        // Sequence 4
        if micro & 0o0010 != 0 {
            // RAR
            let old_link = self.link;
            self.link = (self.ac & 1) != 0;
            self.ac = (self.ac >> 1) | (if old_link { 0o4000 } else { 0 });
        } else if micro & 0o0004 != 0 {
            // RAL
            let old_link = self.link;
            self.link = (self.ac & 0o4000) != 0;
            self.ac = ((self.ac << 1) & BIT_MASK_12) | (old_link as u16);
        } else if micro & 0o0002 != 0 {
            // BSW (PDP-8/E only)
            self.ac = ((self.ac << 6) | (self.ac >> 6)) & BIT_MASK_12;
        }
    }

    // Group two are much more complex and conditions can be chained together with AND and OR depending on the bit set
fn exec_group2(&mut self, micro: u16) {
        let sma       = (micro & 0o0100) != 0; // Corrected: 0o0100
        let sza       = (micro & 0o0040) != 0;
        let snl       = (micro & 0o0020) != 0;
        let and_group = (micro & 0o0010) != 0; // Corrected: 0o0010

        let is_negative = (self.ac & 0o4000) != 0;
        let is_zero = self.ac == 0;
        let is_link_set = self.link;

        let skip = if !and_group {
            // OR group: skip if ANY condition is met
            (sma && is_negative) || (sza && is_zero) || (snl && is_link_set)
        } else {
            // AND group: skip if ALL conditions are met, basically invert the checks
            let spa = sma;
            let sna = sza;
            let szl = snl;
            
            let mut met = true;
            if spa && is_negative { met = false; }
            if sna && is_zero { met = false; }
            if szl && is_link_set { met = false; }
            met
        };
        // Skip no matter what
        if skip || (!sma && !sza && !snl && !and_group){
            self.pc = (self.pc + 1) & BIT_MASK_12;
        }

        // Execution order for Group 2 is Skip -> CLA -> OSR -> HLT 
        if micro & 0o0200 != 0 { self.ac = 0; }
        if micro & 0o0004 != 0 { } 
        if micro & 0o0002 != 0 { self.running = false; }
    }
}

// Simple operation tests TODO
#[test]
fn cpu_tests() {
    let mut test_cpu = Cpu::new();
    test_cpu.running = true;
    
    // Using methods means no `unsafe` block!
    test_cpu.set_value_at_address(1, 1);
    test_cpu.set_value_at_address(2, 63);
    test_cpu.set_value_at_address(3, 5000);
    test_cpu.set_value_at_address(4, 4093);

    test_cpu.op_tad(1);
    assert_eq!(test_cpu.ac, 1);
    
}

// Test the indirect paging 
#[test]
fn test_tad_indirect_page0() {
    let mut cpu = Cpu::new();
    cpu.running = true;
    cpu.pc = 0o200;
    
    cpu.set_value_at_address(0o200, 0o1420); 
    cpu.set_value_at_address(0o020, 0o0500);
    cpu.set_value_at_address(0o500, 0o1234);
    cpu.ac = 0o0001;

    cpu.do_cycle();

    assert_eq!(cpu.ac, 0o1235);
    assert_eq!(cpu.pc, 0o201);
}

// Group2 Logic test
#[test]
fn test_group2_and_logic() {
    let mut cpu = Cpu::new();
    cpu.running = true;
    cpu.pc = 0o200;
    cpu.ac = 0;
    cpu.link = false;

    // SZA (7440) - Skip if AC is zero. 
    // Since AC is zero, it SHOULD skip.
    cpu.set_value_at_address(0o200, 0o7440);
    cpu.do_cycle();
    assert_eq!(cpu.pc, 0o202); // Skipped!

    // SNA SZL (7450) - Skip if AC != 0 AND Link == 0.
    // AC is 0, so SNA is false. In AND group, all must be true.
    // It should NOT skip.
    cpu.pc = 0o200;
    cpu.ac = 0;
    cpu.link = false;
    cpu.set_value_at_address(0o200, 0o7450);
    cpu.do_cycle();
    assert_eq!(cpu.pc, 0o201); // Did not skip, I hope.
}

// Printer/output tests.  We can only really test if the pc is adjusted
#[test]
fn test_iot() {
    let mut cpu = Cpu::new();
    cpu.running = true;
    
    // TSF
    // Instruction 6041: Device 04, Function 1
    cpu.pc = 0o200;
    cpu.set_value_at_address(0o200, 0o6041);
    
    cpu.do_cycle();
    
    assert_eq!(cpu.pc, 0o202);

    // TL6 test
    cpu.pc = 0o300;
    cpu.ac = 0o110; // ASCII 'H'
    cpu.set_value_at_address(0o300, 0o6046);
    
    cpu.do_cycle();
    
    assert_eq!(cpu.pc, 0o301);
    assert_eq!(cpu.ac, 0o110);
}


// Loads file in the form memoryaddress,memoryvalue. Not that our starting value has to be programmed in main()
fn load_file(cpu: &mut Cpu, filename: &str){
    let file = File::open(filename).expect("Unable to find file");
    let reader = BufReader::new(file);

    for line in reader.lines(){
        let line = line.unwrap();
        if line.trim().is_empty() {
            continue;
        }

        let parts: Vec<&str> = line.split(",").collect();
        if parts.len() != 2 {
            continue;
        }

        let address:u16 = u16::from_str_radix(parts[0].replace("0o", "").trim(), 8)
            .expect("Invaid address detected");
        let value:u16 = u16::from_str_radix(parts[1].replace("0o", "").trim(), 8)
            .expect("Invaid value detected detected");
        //println!("{:o} {:o}", address, value);
        cpu.set_value_at_address(address, value);

    }

}

// Main function. We load in our assembled code, set it in the CPUs memory and then touch it off.
fn main() {
    // Get the command line arguments
    let args:Vec<String> =  env::args().collect();
    println!("{:?}", args);
    if args.len() < 2{
        panic!("Insufficient number of command line arguments");
    }
    let filename = args[1].clone(); // Argument 1 should be 
    let starting_number: u16 = args[2].parse().expect("Impossible starting point selected");
    // Usage example:
    let mut cpu = Cpu::new();
    cpu.running = true;
    //cpu.pc = 0o201;
    //let filename:String = String::from("assembledprogram.txt");
    cpu.pc = starting_number;
       
    load_file(&mut cpu, &filename);
    
    let mut total_cycles: u32 = 0;
    while cpu.do_cycle() {
        total_cycles += 1;
    }
    
    println!("Final values");
    println!("PC: {:o} AC: {:o} Link Bit: {} Total cycles: {}", cpu.pc, cpu.ac, cpu.link, total_cycles);
}