import json

# ---------------------------
# Effect Definitions
# ---------------------------

EFFECTS = {
    1: {
        "name": "AdjustResource",
        "fields": [
            ("resource_id", int),
            ("amount", float)
        ]
    },
    2: {
        "name": "AdjustSettlerHealth",
        "fields": [
            ("settler_id", int),
            ("amount", int)
        ]
    },
    3: {
        "name": "AdjustBuildingHealth",
        "fields": [
            ("building_id", int),
            ("amount", float)
        ]
    },
    4: {
        "name": "DamageRandomBuilding",
        "fields": [
            ("building_type", int),
            ("amount", float)
        ]
    },
    5: {
        "name": "InjureRandomSettler",
        "fields": [
            ("amount", int)
        ]
    },
    6: {
        "name": "TechProgress",
        "fields": [
            ("amount", int)
        ]
    },
    7: {
        "name": "TechGained",
        "fields": [
            ("tech_id", int)
        ]
    },
    8: {
        "name": "SettlerArrives",
        "fields": []
    },
    9: {
        "name": "SettlerLeaves",
        "fields": []
    }
}

# ---------------------------
# Helper Functions
# ---------------------------

def parse_list(prompt):
    raw = input(prompt).strip()
    if not raw:
        return []
    return [int(x.strip()) for x in raw.split(",") if x.strip()]

def prompt_field(name, field_type):
    while True:
        try:
            value = input(f"  {name}: ")
            return field_type(value)
        except ValueError:
            print("  Invalid value, try again.")

# ---------------------------
# Effect Builder
# ---------------------------

def create_effect():
    print("\nSelect Effect Type:")

    for key, val in EFFECTS.items():
        print(f"{key}) {val['name']}")

    while True:
        try:
            choice = int(input("Choice: "))
            if choice in EFFECTS:
                break
        except ValueError:
            pass
        print("Invalid choice, try again.")

    effect_def = EFFECTS[choice]
    effect_data = {}

    for field_name, field_type in effect_def["fields"]:
        effect_data[field_name] = prompt_field(field_name, field_type)

    return {
        "type": effect_def["name"],
        "data": effect_data
    }

# ---------------------------
# Event Builder
# ---------------------------

def create_event():
    print("\n--- Creating New Event ---")

    event = {}

    event["id"] = int(input("Event ID: "))
    
    while True:
        prob = float(input("Trigger probability (0.0 - 1.0): "))
        if 0.0 <= prob <= 1.0:
            break
        print("Must be between 0 and 1.")

    event["trigger_probability"] = prob

    event["required_buildings"] = parse_list("Required buildings (comma separated): ")
    event["blocking_buildings"] = parse_list("Blocking buildings: ")
    event["required_techs"] = parse_list("Required techs: ")
    event["blocking_techs"] = parse_list("Blocking techs: ")

    event["effects"] = []

    while True:
        action = input("\nAdd an effect? (y/n): ").lower()
        if action == "n":
            break
        elif action == "y":
            effect = create_effect()
            event["effects"].append(effect)

    return event

# ---------------------------
# Main Loop
# ---------------------------

def main():
    events = []

    print("=== Event Builder ===")

    while True:
        events.append(create_event())

        cont = input("\nCreate another event? (y/n): ").lower()
        if cont != "y":
            break

    filename = input("\nEnter filename (e.g. events.json): ")

    with open(filename, "w") as f:
        json.dump(events, f, indent=2)

    print(f"\nSaved {len(events)} event(s) to {filename}")

# ---------------------------
# Run
# ---------------------------

if __name__ == "__main__":
    main()