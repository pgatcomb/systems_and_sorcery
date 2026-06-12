import csv
import os
from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, TabbedContent, TabPane, DataTable, 
    Input, Button, Select, Checkbox, Static, Log
)
from textual.containers import Vertical, VerticalScroll, Horizontal

# --- CENTRAL DATA STORE ---
db = {
    "resources": {
        0: {"id": 0, "name": "None", "description": "Nothing", "is_roleplay": "FALSE", "is_storable": "FALSE"}
    },
    "techs": {
        0: {"id": 0, "level": 0, "name_level": "Base Tech", "name": "Base Technology", 
            "prerequisites": "0,0,0,0", "named_prerequisite": "None", "requirement": "None",
            "description": "Allows all other techs", "notes": "Base", "research_time": 0}
    },
    "buildings": {},
    "settlers": {}
}

id_counters = {"resources": 1, "techs": 1, "buildings": 0, "settlers": 0}

class SettlementGeneratorApp(App):
    CSS = """
    .form-container { height: auto; padding: 1; border: solid $accent; margin-bottom: 1; }
    .form-row { height: auto; margin-bottom: 1; }
    .section-title { margin-top: 1; color: $secondary; text-style: bold; }
    Input, Select { width: 1fr; margin-right: 1; }
    Button { margin-top: 1; margin-right: 1; }
    DataTable { height: 1fr; border: tall $primary; }
    #log-panel { height: 8; background: $surface; }
    """

    # --- UI GENERATOR HELPERS ---
    def yield_resource_quad(self, prefix, title):
        """Helper generator to stamp out 4 resource/qty inputs quickly."""
        yield Static(f"{title} (Up to 4)", classes="section-title")
        yield Horizontal(
            Select([], prompt=f"{title} 1", id=f"{prefix}_res_1"), Input(placeholder="Qty", id=f"{prefix}_qty_1", value="0"),
            Select([], prompt=f"{title} 2", id=f"{prefix}_res_2"), Input(placeholder="Qty", id=f"{prefix}_qty_2", value="0"),
            classes="form-row"
        )
        yield Horizontal(
            Select([], prompt=f"{title} 3", id=f"{prefix}_res_3"), Input(placeholder="Qty", id=f"{prefix}_qty_3", value="0"),
            Select([], prompt=f"{title} 4", id=f"{prefix}_res_4"), Input(placeholder="Qty", id=f"{prefix}_qty_4", value="0"),
            classes="form-row"
        )

    def compose(self) -> ComposeResult:
        yield Header()
        
        with TabbedContent(id="tabs"):
            
            # --- 1. RESOURCES TAB ---
            with TabPane("Resources", id="tab_resources"):
                with VerticalScroll(classes="form-container"):
                    yield Static("Add New Resource", classes="section-title")
                    with Horizontal(classes="form-row"):
                        yield Input(placeholder="Name (e.g. Wood)", id="res_name")
                        yield Input(placeholder="Description", id="res_desc")
                    with Horizontal(classes="form-row"):
                        yield Checkbox("Is Roleplay?", id="res_roleplay")
                        yield Checkbox("Is Storable?", id="res_storable", value=True)
                    yield Button("Add Resource", id="btn_add_res", variant="success")
                yield DataTable(id="dt_resources")

            # --- 2. TECHS TAB ---
            with TabPane("Techs", id="tab_techs"):
                with VerticalScroll(classes="form-container"):
                    yield Static("Basic Tech Info", classes="section-title")
                    with Horizontal(classes="form-row"):
                        yield Input(placeholder="Tech Name", id="tch_name")
                        yield Input(placeholder="Level (int)", id="tch_level", value="1")
                        yield Input(placeholder="Research Time", id="tch_time", value="10")
                    
                    yield Static("Prerequisites (Up to 4)", classes="section-title")
                    with Horizontal(classes="form-row"):
                        yield Select([], prompt="Prereq 1", id="tch_p1")
                        yield Select([], prompt="Prereq 2", id="tch_p2")
                    with Horizontal(classes="form-row"):
                        yield Select([], prompt="Prereq 3", id="tch_p3")
                        yield Select([], prompt="Prereq 4", id="tch_p4")
                        
                    yield Static("Details", classes="section-title")
                    with Horizontal(classes="form-row"):
                        yield Input(placeholder="Requirement (e.g. None)", id="tch_req", value="None")
                        yield Input(placeholder="Description", id="tch_desc")
                        yield Input(placeholder="Notes", id="tch_notes")
                    yield Button("Add Tech", id="btn_add_tch", variant="success")
                yield DataTable(id="dt_techs")

            # --- 3. BUILDINGS TAB ---
            with TabPane("Buildings", id="tab_buildings"):
                with VerticalScroll(classes="form-container"):
                    yield Static("Basic Info", classes="section-title")
                    with Horizontal(classes="form-row"):
                        yield Input(placeholder="Building Name", id="bld_name")
                        yield Select([], prompt="Tech Required", id="bld_tech")
                        yield Input(placeholder="Build Time", id="bld_time", value="5")
                    
                    yield from self.yield_resource_quad("bld_c", "Resource Costs")
                    yield from self.yield_resource_quad("bld_i", "Inputs")
                    yield from self.yield_resource_quad("bld_o", "Outputs")
                    yield from self.yield_resource_quad("bld_s", "Storage")
                        
                    yield Button("Add Building", id="btn_add_bld", variant="success")
                yield DataTable(id="dt_buildings")

            # --- 4. SETTLERS TAB ---
            with TabPane("Settlers", id="tab_settlers"):
                with VerticalScroll(classes="form-container"):
                    yield Static("Add New Settler", classes="section-title")
                    with Horizontal(classes="form-row"):
                        yield Input(placeholder="Name", id="set_name")
                        yield Input(placeholder="Age", id="set_age", value="25")
                        yield Input(placeholder="Health", id="set_health", value="100")
                        yield Input(placeholder="Stamina", id="set_stamina", value="100")
                    with Horizontal(classes="form-row"):
                        yield Input(placeholder="Build Skill", id="set_build", value="50")
                        yield Input(placeholder="Work Skill", id="set_work", value="50")
                        yield Input(placeholder="Research Skill", id="set_research", value="50")
                    with Horizontal(classes="form-row"):
                        yield Select([], prompt="Affinity (Likes)", id="set_affinity")
                        yield Select([], prompt="Aversion (Dislikes)", id="set_aversion")
                    yield Button("Add Settler", id="btn_add_set", variant="success")
                yield DataTable(id="dt_settlers")

        # Global Actions
        with Horizontal(classes="form-row"):
            yield Button("💾 SAVE ALL TO CSV FILES", id="btn_save_all", variant="error")
        yield Log(id="log-panel")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#dt_resources", DataTable).add_columns("ID", "Name", "Desc", "Roleplay", "Storable")
        self.query_one("#dt_techs", DataTable).add_columns("ID", "Level", "Name", "Prereqs", "Time")
        self.query_one("#dt_buildings", DataTable).add_columns("ID", "Name", "Tech", "Costs", "Inputs", "Outputs")
        self.query_one("#dt_settlers", DataTable).add_columns("ID", "Name", "Age", "Skills", "Affinity", "Aversion")
        
        self.query_one("#dt_resources", DataTable).add_row(0, "None", "Nothing", "FALSE", "FALSE")
        self.query_one("#dt_techs", DataTable).add_row(0, 0, "Base Technology", "None", 0)

        self.update_dropdowns()

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated):
        self.update_dropdowns()

    def update_dropdowns(self):
        """Updates all 20+ dropdowns with the latest in-memory data."""
        tech_options = [(f"{t['id']}: {t['name']}", t['id']) for t in db["techs"].values()]
        res_options = [(f"{r['id']}: {r['name']}", r['id']) for r in db["resources"].values()]

        # Techs
        for i in range(1, 5):
            self.query_one(f"#tch_p{i}", Select).set_options(tech_options)
        
        # Buildings
        self.query_one("#bld_tech", Select).set_options(tech_options)
        for prefix in ["bld_c", "bld_i", "bld_o", "bld_s"]:
            for i in range(1, 5):
                self.query_one(f"#{prefix}_res_{i}", Select).set_options(res_options)
        
        # Settlers
        self.query_one("#set_affinity", Select).set_options(res_options)
        self.query_one("#set_aversion", Select).set_options(res_options)

    # --- STRING MAGIC HELPERS FOR ARRAYS ---

    def safe_int(self, value, default=0):
        try: return int(value)
        except (ValueError, TypeError): return default

    def get_select_val(self, target_id):
        """
        BULLETPROOF FIX: Safely gets Select values. 
        If the dropdown is completely untouched, Textual returns an internal object (Select.NULL) 
        which crashes the script. This forces ANY non-integer value down to a safe 0 ("None").
        """
        try:
            val = self.query_one(target_id, Select).value
            return int(val)
        except (ValueError, TypeError, Exception):
            return 0

    def build_tech_prereq_strings(self, p_ids):
        """Packs up to 4 Tech IDs into '1,2,0,0' and 'Tech1, Tech2' formats."""
        valid_ids, valid_names = [], []
        for t_id in p_ids:
            if t_id != 0:
                valid_ids.append(str(t_id))
                valid_names.append(db['techs'][t_id]['name'])
                
        # Pad right side to ensure exactly 4 elements
        while len(valid_ids) < 4:
            valid_ids.append("0")
            
        return ",".join(valid_ids), ", ".join(valid_names) if valid_names else "None"

    def build_resource_strings(self, res_qty_pairs):
        """Packs up to 4 Res/Qty pairs into '1:5,2:10,0:0,0:0' and '5 Wood, 10 Stone'."""
        valid_strs, valid_names = [], []
        for r_id, qty in res_qty_pairs:
            if r_id != 0:
                valid_strs.append(f"{r_id}:{qty}")
                valid_names.append(f"{qty} {db['resources'][r_id]['name']}")
                
        # Pad right side to ensure exactly 4 elements
        while len(valid_strs) < 4:
            valid_strs.append("0:0")
            
        return ",".join(valid_strs), ", ".join(valid_names) if valid_names else "None"

    # --- BUTTON LOGIC ---

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one(Log)
        
        if event.button.id == "btn_add_res":
            name = self.query_one("#res_name", Input).value
            if not name: return log.write_line("❌ Resource Name is required!")
            r_id = id_counters["resources"]
            db["resources"][r_id] = {
                "id": r_id, "name": name, "description": self.query_one("#res_desc", Input).value or "None",
                "is_roleplay": "TRUE" if self.query_one("#res_roleplay", Checkbox).value else "FALSE",
                "is_storable": "TRUE" if self.query_one("#res_storable", Checkbox).value else "FALSE"
            }
            self.query_one("#dt_resources", DataTable).add_row(r_id, name, db["resources"][r_id]["description"], db["resources"][r_id]["is_roleplay"], db["resources"][r_id]["is_storable"])
            id_counters["resources"] += 1
            self.query_one("#res_name", Input).value = ""
            log.write_line(f"✅ Resource added: {name}")

        elif event.button.id == "btn_add_tch":
            name = self.query_one("#tch_name", Input).value
            if not name: return log.write_line("❌ Tech Name is required!")
            
            t_id = id_counters["techs"]
            lvl = self.safe_int(self.query_one("#tch_level", Input).value)
            
            p_ids = [self.get_select_val(f"#tch_p{i}") for i in range(1, 5)]
            prereq_str, prereq_names = self.build_tech_prereq_strings(p_ids)
            
            db["techs"][t_id] = {
                "id": t_id, "level": lvl, "name_level": f"{name} {lvl}", "name": name,
                "prerequisites": prereq_str, "named_prerequisite": prereq_names,
                "requirement": self.query_one("#tch_req", Input).value or "None",
                "description": self.query_one("#tch_desc", Input).value or "None",
                "notes": self.query_one("#tch_notes", Input).value or "None",
                "research_time": self.safe_int(self.query_one("#tch_time", Input).value)
            }
            self.query_one("#dt_techs", DataTable).add_row(t_id, lvl, name, prereq_names, db["techs"][t_id]["research_time"])
            id_counters["techs"] += 1
            self.query_one("#tch_name", Input).value = ""
            log.write_line(f"✅ Tech added: {name}")

        elif event.button.id == "btn_add_bld":
            name = self.query_one("#bld_name", Input).value
            if not name: return log.write_line("❌ Building Name required!")

            b_id = id_counters["buildings"]
            t_id = self.get_select_val("#bld_tech")

            def extract_quad(prefix):
                pairs = []
                for i in range(1, 5):
                    r_id = self.get_select_val(f"#{prefix}_res_{i}")
                    qty = self.safe_int(self.query_one(f"#{prefix}_qty_{i}", Input).value)
                    pairs.append((r_id, qty))
                return self.build_resource_strings(pairs)

            cost_str, cost_names = extract_quad("bld_c")
            in_str, in_names = extract_quad("bld_i")
            out_str, out_names = extract_quad("bld_o")
            store_str, store_names = extract_quad("bld_s")

            db["buildings"][b_id] = {
                "id": b_id, "full_name": name,
                "tech_required": t_id, "tech_required_name": db["techs"][t_id]["name"],
                "resource_costs_names": cost_names, "resource_costs": cost_str,
                "input_names": in_names, "input": in_str,
                "output_names": out_names, "output": out_str,
                "storage_names": store_names, "storage": store_str, 
                "construction_time": self.safe_int(self.query_one("#bld_time", Input).value)
            }
            self.query_one("#dt_buildings", DataTable).add_row(b_id, name, db["techs"][t_id]["name"], cost_names, in_names, out_names)
            id_counters["buildings"] += 1
            self.query_one("#bld_name", Input).value = ""
            log.write_line(f"✅ Building added: {name}")

        elif event.button.id == "btn_add_set":
            name = self.query_one("#set_name", Input).value
            if not name: return log.write_line("❌ Settler Name required!")

            s_id = id_counters["settlers"]
            aff_id = self.get_select_val("#set_affinity")
            ave_id = self.get_select_val("#set_aversion")

            db["settlers"][s_id] = {
                "id": s_id, "name": name,
                "age": self.safe_int(self.query_one("#set_age", Input).value),
                "stamina": self.safe_int(self.query_one("#set_stamina", Input).value),
                "health": self.safe_int(self.query_one("#set_health", Input).value),
                "build_skill": self.safe_int(self.query_one("#set_build", Input).value),
                "work_skill": self.safe_int(self.query_one("#set_work", Input).value),
                "research_skill": self.safe_int(self.query_one("#set_research", Input).value),
                "resource_affinity": aff_id, "resource_affinity_name": db["resources"][aff_id]["name"],
                "resource_aversion": ave_id, "resource_aversion_name": db["resources"][ave_id]["name"]
            }
            b, w, r = db["settlers"][s_id]["build_skill"], db["settlers"][s_id]["work_skill"], db["settlers"][s_id]["research_skill"]
            self.query_one("#dt_settlers", DataTable).add_row(s_id, name, db["settlers"][s_id]["age"], f"{b}/{w}/{r}", db["resources"][aff_id]["name"], db["resources"][ave_id]["name"])
            id_counters["settlers"] += 1
            self.query_one("#set_name", Input).value = ""
            log.write_line(f"✅ Settler added: {name}")

        elif event.button.id == "btn_save_all":
            self.export_all_csvs()

    def export_all_csvs(self):
        log = self.query_one(Log)
        files = {
            "resources.csv": ["id", "name", "description", "is_roleplay", "is_storable"],
            "techs.csv": ["id", "level", "name_level", "name", "prerequisites", "named_prerequisite", "requirement", "description", "notes", "research_time"],
            "buildings.csv": ["id", "full_name", "tech_required", "tech_required_name", "resource_costs_names", "resource_costs", "input_names", "input", "output_names", "output", "storage", "storage_names", "construction_time"],
            "settlers.csv": ["id", "name", "age", "stamina", "health", "build_skill", "work_skill", "research_skill", "resource_affinity", "resource_affinity_name", "resource_aversion", "resource_aversion_name"]
        }
        try:
            for filename, headers in files.items():
                dict_key = filename.split('.')[0]
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=headers, delimiter='\t' if '\t' in headers[0] else ',')
                    writer.writeheader()
                    for item in db[dict_key].values():
                        writer.writerow(item)
            log.write_line("[bold green]✅ SUCCESS: ALL 4 FILES GENERATED IN CURRENT FOLDER.[/bold green]")
        except Exception as e:
            log.write_line(f"[bold red]❌ ERROR SAVING FILES: {e}[/bold red]")

if __name__ == "__main__":
    app = SettlementGeneratorApp()
    app.run()