from datetime import datetime
from textual.app import App
from textual.widgets import Footer, Input, DataTable, Static, Header
from textual.containers import Horizontal, Vertical
from escpos import printer
import random
from struct import struct
import time


class CashRegister(App):
    TAX_PCT = 0.0635
    TITLE = "CASH REGISTER"
    BINDINGS = [
        ("escape", "quit", "Quit"),
        ("shift+f1", "print_and_post", "Print & Post"),
        ("shift+f2", "print_bol", "Print Bill of Lading"),
    ]

    def action_print_bol(self):
        self.print_bill_of_lading()

    def print_bill_of_lading(self):
            table = self.query_one("#receipt_tape", DataTable)
            if not table.rows:
                self.notify("Manifest is empty!", severity="error")
                return

            total_value = 0.0
            total_tonnage = 0
            receipt_lines = []

            # --- HEADER ---
            receipt_lines.append("========================")
            receipt_lines.append(" IMPERIAL PORT AUTHORITY")
            receipt_lines.append("     BILL OF LADING     ")
            receipt_lines.append("========================")
            receipt_lines.append(f"DT: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            receipt_lines.append(f"PORT: X-{random.randint(100, 999)}-{random.choice(['ALPHA', 'BETA', 'PRIME'])}")
            receipt_lines.append(f"VESSEL: REG-{random.randint(1000, 9999)}")
            receipt_lines.append("------------------------")
            receipt_lines.append("CARGO MANIFEST:")

            # --- CARGO LINES ---
            for row_key in table.rows:
                item, qty, price, line_total = table.get_row(row_key)
                # Truncate item name to 24 chars to prevent ugly wrapping
                item_name = str(item).upper()[:24] 
                
                receipt_lines.append(f"[{qty} dT] {item_name}")
                receipt_lines.append(f"  @ {price:,.0f}c/dT")
                receipt_lines.append(f"  VAL: {line_total:,.0f}c")
                
                total_value += line_total
                total_tonnage += qty

            # --- CALCULATE FEES ---
            # Brokerage Fee: 5% of total cargo value
            broker_fee = total_value * 0.05
            # Customs Tariff: 2% of total cargo value
            customs_tariff = total_value * 0.02
            # Berthing/Handling: Flat 500 + 10 per displacement ton
            handling_fee = 500.0 + (total_tonnage * 10.0)
            
            grand_total = total_value + broker_fee + customs_tariff + handling_fee

            # --- FOOTER & TOTALS ---
            receipt_lines.append("------------------------")
            receipt_lines.append(f"TOTAL TONNAGE: {total_tonnage} dT")
            receipt_lines.append(f"CARGO VALUE:  {total_value:,.0f}c")
            receipt_lines.append("------------------------")
            receipt_lines.append("FEES & TARIFFS:")
            receipt_lines.append(f"BROKER (5%):  {broker_fee:,.0f}c")
            receipt_lines.append(f"CUSTOMS (2%): {customs_tariff:,.0f}c")
            receipt_lines.append(f"HANDLING:     {handling_fee:,.0f}c")
            receipt_lines.append("========================")
            receipt_lines.append(f"TOTAL DUE:    {grand_total:,.0f}c")
            receipt_lines.append("========================")
            receipt_lines.append("\nCLEARED FOR DEPARTURE")
            receipt_lines.append("\n\n")

            # --- PRINT ROUTINE ---
            try:
                pr = printer.Win32Raw("Generic / Text Only")
                pr.set(custom_size=True, width=2, height=2, align="left")
                pr.open()
                pr.set(align="center")
                pr.qr("https://travellermap.com/?p=14.455%21-107.338%218.25")
                # Print the text
                pr.set(align="left")
                pr.text("\n".join(receipt_lines))
                
                # Add some official looking barcodes
                pr.set(align="center")
                pr.text("MANIFEST ID:\n")
                # EAN13 requires exactly 12 digits (it calculates the 13th)
                pr.barcode(code=str(random.randint(100000000000, 999999999999)), bc="EAN13")
                pr.text("\nCUSTOMS AUTH:\n")
                pr.barcode(code=str(random.randint(100000000000, 999999999999)), bc="EAN13")
                
                pr.cut()
                pr.close()
                
                # Clear the register for the next transaction
                table.clear()
                self.update_total()
                self.notify("Bill of Lading printed successfully.")
                
            except Exception as e:
                self.notify(f"Printer error: {e}", severity="error")

    def __init__(self):
        self.subtotal = 0.0
        self.tax_amount = 0.0
        self.total = 0.0
        super().__init__()


    def compose(self):
        yield Header(show_clock=True)
        yield Footer()
        with Vertical():
            with Horizontal(id="horzarea"):
                yield Input(id="item", placeholder="Item")
                yield Input(id="qty", placeholder="Qty", type="integer")
                yield Input(id="price", placeholder="Price", type="number")
            yield DataTable(id="receipt_tape")
            yield Static("TOTAL: $0.00 TAX: $0.00 TOTAL: $0.00", id="total_display")

    def on_mount(self):
        self.query_one("#item").focus()
        self.query_one("#item").styles.width="2fr"
        self.query_one("#qty").styles.width="1fr"
        self.query_one("#price").styles.width="1fr"
        table = self.query_one("#receipt_tape", DataTable)
        table.add_columns("Item", "Qty", "Price", "Total")
        table.height = "5fr"
        table.cursor_type = "row"
        self.query_one("#horzarea").styles.height="2fr"
        self.query_one("#total_display").styles.height="1fr"
    
    def on_data_table_row_selected(self, e):
        if e.data_table.id == "receipt_tape":
            e.data_table.remove_row(e.row_key)
            self.update_total()

    def update_total(self):
        table = self.query_one("#receipt_tape", DataTable)
        self.subtotal = sum(table.get_row(row_key)[3] for row_key in table.rows)
        self.tax_amount = self.subtotal * CashRegister.TAX_PCT
        self.total = self.subtotal + self.tax_amount
        self.query_one("#total_display").update(f"SUBTOTAL: ${self.subtotal:.2f} TAX: ${self.tax_amount:.2f} TOTAL: ${self.total:.2f}")

    def on_input_submitted(self, event: Input.Submitted):
        # When they hit ENTER on the price field...
        if event.input.id == "price":
            item = self.query_one("#item").value
            qty = int(self.query_one("#qty").value or 1)
            price = float(self.query_one("#price").value or 0.0)
            
            # Add to table
            table = self.query_one("#receipt_tape", DataTable)
            table.add_row(item, qty, price, qty * price)
            
            # CLEAR fields and set focus back to Item for the next rapid-fire entry
            self.query_one("#item").value = ""
            self.query_one("#qty").value = ""
            self.query_one("#price").value = ""
            self.query_one("#item").focus()            
            self.update_total()
        elif event.input.id == "item":
            self.query_one("#qty").focus()
        elif event.input.id == "qty":
            self.query_one("#price").focus()

    def action_print_and_post(self):
        self.print_and_post()

    def print_and_post(self):
        # TODO Post the transaction using wb to a continuous file, the structure still needs to be decided, do not do this yet
        table = self.query_one("#receipt_tape", DataTable)
        if not table.rows:
            self.notify("No items in receipt!", severity="error")
            return
        timestamp = int(time.time())
        record_structure = "< Q Q Q Q"
        with open("transactions.data", "ab"):
            struct.pack(record_structure,items_sold, timestamp, self.subtotal, self.tax, self.total)

        total = 0.0
        items_sold = 0
        receipt_lines = []
        receipt_lines.append("SHOP")
        receipt_lines.append(datetime.now().strftime("%Y-%m-%d %I:%M %p"))
        receipt_lines.append("-" * 24)

        for row_key in table.rows:
            item, qty, price, line_total = table.get_row(row_key)
            receipt_lines.append(f"{item.upper()}")
            receipt_lines.append(f"{qty} @ {price:.2f}     {line_total:.2f}")
            total += line_total
            items_sold += qty
        receipt_lines.append("-" * 24)
        receipt_lines.append(f"ITEMS SOLD: {items_sold}\n")
        receipt_lines.append(f"SUBTOTAL: {self.subtotal:.2f} \nTAX: {self.tax_amount:.2f} \nTOTAL: {self.total:.2f}")
        receipt_lines.append("\n\nTHANK YOU FOR\nYOUR PATRONAGE")
        receipt_lines.append("\n\n\n\n")

        try:
            pr = printer.Win32Raw("Generic / Text Only")
            pr.set(custom_size=True, width=2, height=2,align="center")
            pr.open()
            text = """
 +-+-+-+-+-+
 |S|T|O|R|E|
 +-+-+-+-+-+
                  """
            pr.text(text + "\n")
            
            pr.text("\n".join(receipt_lines))
            pr.barcode(code=str(random.randint(100000000000, 999999999999)),bc="EAN13")
            pr.cut()
            pr.close()
            table.clear()
            self.update_total()
            self.notify("Receipt printed and order cleared.")
        except Exception as e:
            self.notify(f"Printer error: {e}", severity="error")


if __name__ == "__main__":
    app = CashRegister()
    app.run()