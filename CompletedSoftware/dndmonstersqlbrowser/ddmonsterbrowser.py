'''
dnd sqlite monster filter tool
version 1.0
This tool automatically opens up a database 'ddmonsters.db' and spools up a textual
interface consisting of a textbox where users can enter detailed filters that are automatically
translated into sqlite queries that update the displayed data in the table below. If an item in the table
is clicked, it updates a STATIC at the bottom with a cleaner view of that data
--------------------------------------
TEXT INPUT FOR QUERIES | FILTER BUTTON
--------------------------------------
DATATABLE with
Monstername, ac, etc.
--------------------------------------
STATIC with details about monster, e.g.
HP, ac, etc.
--------------------------------------
'''
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, DataTable, TextArea, Header, Footer
#from textual import event
import sqlite3

FILENAME = "ddmonsters.db"


def connect_to_db(filepath):
    conn = sqlite3.connect(filepath)
    cur = conn.cursor()

    # Get count
    cur.execute("SELECT COUNT(*) FROM ddmonsters")
    row = cur.fetchone()
    print(f"{row[0]} entries loaded")

    return conn


class MonsterApp(App):
    TITLE = "MONSTER DATABASE APP"
    BINDINGS = [("q", "quit", "Quit")]
    CSS_PATH = "mbcss.tcss"
    def compose(self):
        yield Header(show_clock=True, id="the_header")
        with Vertical(id="vertical_area"):
            yield Input(placeholder="Search Query",id="search_query")
            yield DataTable(id="monster_datatable")
            yield TextArea("Your text goes here", id="monster_details")

        yield Footer()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        if "drop" in query.lower():
            return
        query = "SELECT * FROM ddmonsters WHERE " + query
        try:
            table = self.query_one("#monster_datatable")
            table.clear(columns=False)

            cur = conn.execute(query)
            rows = cur.fetchall()

            for row in rows:
                table.add_row(*[str(x) for x in row])

        except Exception as e:
            ta = self.query_one("#monster_details")
            ta.text = f"ERROR:\n{e}"



    def populate_table(self):
        # Filtering rules will go here later
        table = self.query_one("#monster_datatable")
        table.clear(columns=False)
        cur = conn.execute('SELECT * FROM ddmonsters')
        for item in cur.fetchall():
            table.add_row(*item)

    def on_mount(self):
        table = self.query_one("#monster_datatable")
        table.cursor_type = "row"
        cur = conn.execute('PRAGMA table_info("ddmonsters")')
        columns = cur.fetchall()
        column_names = [str(col[1]) for col in columns]
        table.add_columns(*column_names)
        self.populate_table()
        self.current_sort_column = None
        self.is_descending = False

    def on_data_table_row_highlighted(self, event: DataTable.RowSelected) -> None:
        table = event.data_table
        row_values = table.get_row(event.row_key)
        ta = self.query_one("#monster_details")
        ta.text = f"""Monster name : {row_values[0].title()} | Type: {row_values[2].title()} | Size: {row_values[3]} | Alignment: {row_values[7]} | Source: {row_values[9]}
Challenge Rating: {row_values[1]} | AC: {row_values[4]} | HP: {row_values[5]} | {row_values[8]}
Str/Dex/Con/Wis/Int/Cha: {row_values[10]}/{row_values[11]}/{row_values[12]}/{row_values[13]}/{row_values[14]}/{row_values[15]}
        """
        
    @on(DataTable.HeaderSelected)
    def sort_column_toggle(self, event: DataTable.HeaderSelected) -> None:
        table = self.query_one(DataTable)
        
        if self.current_sort_column != event.column_key:
            self.current_sort_column = event.column_key
            self.is_descending = True
        else:
            self.is_descending = not self.is_descending
        def null_safe_sort_key(value):
            if value is None or value == "":
                return (1, None)

            try:
                # Try numeric conversion
                num = float(value)
                return (0, num)
            except ValueError:
                # Fallback to string
                return (0, str(value))

        table.sort(
            event.column_key, 
            key=null_safe_sort_key, 
            reverse=self.is_descending
        )


if __name__ == "__main__":
    try:
        conn = connect_to_db(FILENAME)
    except:
        print(f"{FILENAME} not found.")
        raise FileNotFoundError
    my_app = MonsterApp()
    my_app.run()
    conn.close()
