# Rusty8 PDP-8 Emulator

This project emulates the DEC PDP-8 hardware and software interpretation.  It works by importing 
memory addresses and values from a separate python assembly program and then outputs the appropriate
values following running.


### Features
* **Hardware emulation** of the DEC PDP-8 Group 1 and 2 Opcodes and primary operators
* **Python based assembler** for converting simple text files containing PDP-8 assembly into memory
* **12-bit simulation** using the default primitives in rust with careful bit masking

## Usage
1. Write your PDP-8 assembly code in a text file
2. Using the command line, execute:
  'python rusty_assembler.py <your filename>'
3. When this is finished, run the pdp-8 simulation using
  'rusty8 assembledprogram.txt <starting memory address>'

The output will appear in the terminal.
