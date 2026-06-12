class Resource:
    def __init__(self, name, storable=True):
        self.name = name
        self.storable = True if storable else False
    def __str__(self):
        return self.name

class Building:
    def __init__(self, name:str, produces:dict, consumes:dict, holds:dict):
        self.name = name
        self.produces = produces
        self.consumes = consumes
        self.capacities = holds
        self.produced = False

power = Resource("Power", False)
water = Resource("Water")
labor = Resource("Labor", False)
food = Resource("Food")
fuel = Resource("Fuel")

hunting_camp = Building("Hunting Camp", {food: 10}, {labor: 4}, {food:20})
pumping_station = Building("Water Pumping Station", {water: 10}, {power: 5, labor : 1}, {water:100})
diesel_generator = Building("Diesel Generator", {power: 30}, {labor:1, fuel:5}, {fuel: 100})
water_tank = Building("Water tank", {}, {}, {water: 1000})

settlement_new = [hunting_camp, pumping_station, diesel_generator, water_tank, hunting_camp]

def calculate_storage(plot:list):
    capacities = {}
    for building in plot:
        for resource, amount in building.capacities.items():
            if resource not in capacities.keys():
                capacities[resource] = amount
            else:
                capacities[resource] += amount
    return capacities

def calculate_production(plot:list):
    production = {}
    for building in plot:
        for resource, amount in building.produces.items():
            if resource not in production.keys():
                production[resource] = amount
            else:
                production[resource] += amount
    return production

def calculate_runs(building: Building, available_resources:dict):
    conditions = 0
    for resource, amount in building.consumes.items():
        # Can't run if a resource is completely missing
        if resource not in available_resources.keys():
            return False
        if available_resources[resource] >= amount:
            conditions += 1
    return conditions >= len(building.consumes)

def apply_run(building:Building, current_production:dict) -> dict:
    for item, amount in building.consumes.items():
        current_production[item] -= amount
        print(f"{building.name} consumed {amount} of {item}")
    for item, amount in building.produces.items():
        current_production[item] += amount
        print(f"{building.name} produced {amount} of {item}")
    return current_production

def calculate_total_production(settlement, labor_available:int):
    # 1 Aggregate production for all
    total_production = calculate_production(settlement)
    total_production[labor] = labor_available
    
    round_counter = 0
    while True:
        print(f"Round: {round_counter}")
        round_counter += 1
        changed = False
        # iterate through each building
        for building in settlement:
            # Do we have enough resources right this second to utilize and can that building actually do work?
            if calculate_runs(building, total_production) and not building.produced:
                total_production = apply_run(building, total_production)
                building.produced = True
                changed = True

        if not changed:
            break
    print("final results")
    for item, amount in total_production.items():
        print(f"{item}: {amount}")

calculate_total_production(settlement_new, 25)