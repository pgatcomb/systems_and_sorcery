# ESC/POS Python Printer Application (Textual POS)

A TUI (Terminal User Interface) application built with [Textual](https://textual.textualize.io/) designed to interface with ESC/POS compatible thermal printers using the Windows print spooler.

## Overview

This program allows users to quickly generate and print content to thermal printers. It provides two distinct modes: a free-form text mode for general notes and a structured receipt mode for itemized billing and calculations.

## Features

- **Dual Operation Modes**:
    - **Basic Printing Tab**: A simple text area for entering and printing raw text strings.
    - **Receipt Printing Tab**: A structured interface for itemized entries.
- **Receipt Management**:
    - **Itemized Entry**: Add items with specific names, quantities, and costs.
    - **Automated Totals**: Automatically calculates line item totals and the overall grand total.
    - **Interactive Table**: A `DataTable` view where you can click or select a row to remove it from the receipt.
- **Printer Controls**:
    - **PRINT**: Smart printing based on the active tab (sends text or a formatted receipt).
    - **CUT**: Issues a hardware cut command (`GS V 0`) to the printer.
    - **NEW**: Quickly clears all inputs, text areas, and table rows.
- **Windows Integration**: Uses the `pywin32` library to send RAW data directly to the default Windows printer.

## Prerequisites

- **OS**: Windows (Required for `win32print` integration).
- **Hardware**: An ESC/POS compatible thermal printer installed as a Windows printer.
- **Python Libraries**:
    ```bash
    pip install textual pywin32
    ```

## Usage

1. **Launch**: Run the application via the terminal:
   ```bash
   python ppos.py
   ```
2. **Select Mode**: Use the tabs at the top to switch between "Basic Printing" and "Receipt Printing."
3. **Add Items**: In Receipt mode, fill in the Name, QTY, and COST fields, then press **ADD**.
4. **Print**: Click the **PRINT** button at the bottom. By default, it will target your system's default printer.
