from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, TextArea, TabbedContent, TabPane, DataTable, Input, Header

import win32print
#import win32api

class EscPosPrinter:
    def __init__(self, printer_name: str | None = None):
        # Use default printer if none specified
        self.printer_name = printer_name or win32print.GetDefaultPrinter()
        self.handle = None

    def open(self) -> None:
        self.handle = win32print.OpenPrinter(self.printer_name)
        win32print.StartDocPrinter(
            self.handle,
            1,
            ("Textual POS Print", None, "RAW")
        )
        win32print.StartPagePrinter(self.handle)

    def close(self) -> None:
        if self.handle:
            win32print.EndPagePrinter(self.handle)
            win32print.EndDocPrinter(self.handle)
            win32print.ClosePrinter(self.handle)
            self.handle = None

    def write(self, data: bytes) -> None:
        win32print.WritePrinter(self.handle, data)

    def lprint(self, line: str = "") -> None:
        """
        Equivalent of BASIC LPRINT.
        Sends one line plus newline.
        """
        if not self.handle:
            raise RuntimeError("Printer not opened")

        # ESC/POS expects CRLF
        payload = (line + "\r\n").encode("ascii", errors="replace")
        self.write(payload)

    def cut(self) -> None:
        # Full cut: GS V 0
        self.write(b"\x1d\x56\x00")


class PrinterApp(App):

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with TabbedContent(id="tabs"):
                with TabPane("Basic Printing", id="simple"):
                    yield TextArea()

                with TabPane("Receipt Printing", id="receipt"):
                    with Horizontal(id="itemadd"):
                        yield Input(placeholder="Item Name",id="receiptitemname")
                        yield Input(placeholder="QTY",type="number",id="receiptitemqty")
                        yield Input(placeholder="COST",type="number",id="receiptitemcost")
                        yield Button("ADD",id="addtoreceipt")
                    yield DataTable(id="receiptview")

            with Vertical(id="buttons"):
                with Horizontal(id="printcut"):
                    yield Button("PRINT",id="PRINT")
                    yield Button("CUT",id="CUT")
                with Horizontal(id="newloadsave"):
                    yield Button("NEW",id="NEW")
                    yield Button("LOAD",id="LOAD")
                    yield Button("SAVE",id="SAVE")

    def on_mount(self) -> None:
        # Buttons: fixed at bottom
        buttons = self.query_one("#buttons")
        buttons.styles.dock = "bottom"
        buttons.styles.height = 7
        buttons.styles.align_horizontal = "center"

        ia = self.query_one("#itemadd")
        ia.styles.height = 3
        ia.styles.dock = "top"
        ia.styles.align_horizontal = "center"


        inputs = self.query("#itemadd Input")
        inputs[0].styles.width = "4fr"   # Item name
        inputs[1].styles.width = "2fr"    # QTY
        inputs[2].styles.width = "2fr"    # COST


        hor = self.query_one("#printcut")
        hor.styles.align_horizontal = "center" 
        hor = self.query_one("#newloadsave") 
        hor.styles.align_horizontal = "center" 

        # Tabs: fill remaining space
        self.query_one("#tabs").styles.dock = "top"

        column_names = [("Item", "Qty", "Amount", "Total")]

        table = self.query_one("#receiptview")
        table.add_columns("Item", "Qty", "Cost", "Total")
        table = self.query_one("#receiptview", DataTable)
        table.cursor_type = "row"
        table.show_cursor = True

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.data_table.remove_row(event.row_key)

    def add_item_to_receipt(self) -> None:
            name = self.query_one("#receiptitemname", Input).value
            qty = self.query_one("#receiptitemqty", Input).value
            cost = self.query_one("#receiptitemcost", Input).value
            if (name == "" or qty == "" or cost == ""):
                return
            total = int(qty) * float(cost)
            table = self.query_one("#receiptview")
            table.add_row(name, qty,cost,total)

            # Later:
            # - validate input
            # - append to ListView
            # - recompute totals

    def print_simple_text(self) -> None:
        text = self.query_one(TextArea).text

        printer = EscPosPrinter()
        printer.open()

        for line in text.splitlines():
            printer.lprint(line)

       # printer.cut() Handled elsewhere when needed
        printer.close()

    def print_receipt(self) -> None:
        table = self.query_one("#receiptview", DataTable)

        printer = EscPosPrinter()
        printer.open()

        # Header
        printer.lprint("MY STORE")
        printer.lprint("------------------------------")

        total = 0.0

        for row_key in table.rows:
            row = table.get_row(row_key)
            item, qty, cost, line_total = row

            printer.lprint(f"{item:<15}{qty:>3}{float(cost):>7.2f}{line_total:>7.2f}")
            total += float(line_total)

        printer.lprint("------------------------------")
        printer.lprint(f"{'TOTAL':<20}{total:>10.2f}")

        printer.close()

    def do_print(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        current_tab_id = tabs.active
        if current_tab_id == "simple":
            self.notify("Printing Simple Text")
            self.print_simple_text()
        else:
            self.notify("Printing Receipt Text")
            self.print_receipt()

    def do_cut(self) -> None:
        print("CUT pressed")
        printer = EscPosPrinter()
        printer.open()
        printer.cut()
        printer.close()

    def do_new(self) -> None:
        self.notify("Clearing View")
        self.query_one("#receiptview").clear(columns=False)
        self.query_one(Input).clear()
        self.query_one(TextArea).clear()


    def do_load(self) -> None:
        print("LOAD pressed")
        # open file dialog, load text or receipt template

    def do_save(self) -> None:
        print("SAVE pressed")
        # save current context appropriately

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        match button_id:
            case "addtoreceipt":
                self.add_item_to_receipt()

            case "PRINT":
                self.do_print()

            case "CUT":
                self.do_cut()

            case "NEW":
                self.do_new()

            case "LOAD":
                self.do_load()

            case "SAVE":
                self.do_save()

if __name__ == "__main__":
    PrinterApp().run()
