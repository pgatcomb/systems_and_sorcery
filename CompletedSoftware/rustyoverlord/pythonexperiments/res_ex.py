class Resource:
    def __init__(self, id:int, name:str, description:str, is_storable:bool, is_stat:bool):
        """Instantiates a resource object"""
        self.id = int(id)
        self.name = name
        self.description = description
        self.storable = True if is_storable else False
        self.is_stat = True if is_stat  else False
    
    def __str__(self):
        return self.name

class Settler:
    def __init__(self, id:int, name:str, stats:dict, produces:dict, consumes:dict):
        """Instantiates a settler object with basic information"""
        self.id = int(id)
        self.name = name
        self.stats = stats
        self.produces = produces
        self.consumes = consumes

class Building:
    def __init__(self, id:int, name:str, description:str, produces:dict, consumes:dict, max_contains:dict):
        self.id = int(id)
        self.name = name
        self.description = description
        self.produces = produces
        self.consumes = consumes
        self.max_contains = max_contains
        self.contains = {}
        for key in self.max_contains.keys():
            self.contains[key] = 0
    
    def get_raw_production(self):
        for key, value in self.produces.items():
            print(f"{key}: {value}")

    def get_raw_consumption(self):
        for key, value in self.consumes.items():
            print(f"{key}: {value}")

    def update_storage(self, resource:Resource, quantity):
        if resource in self.contains:
            self.contains[resource] += quantity
            if self.contains[resource] >= self.max_contains[resource]:
                self.contains[resource] = self.max_contains[resource]
            elif self.contains[resource] <= 0:
                self.contains[resource] = 0



health = Resource(0, "Health", "Overall health", False, True)
age = Resource(1, "Age", "A person's age", False, True)
cash = Resource(2, "Cash", "Measure of financial wealth", True, False)
food = Resource(3, "Food", "Available food", True, True)
hunger = Resource(4, "Hunger", "Feeling of being hungry", False, True)
thirst = Resource(5, "Thirst", "Feeling of being thirsty", False, True) 
water = Resource(6, "Water", "Potable Water", True, False)
labor = Resource(7, "Labor", "Measure of productivity", False, False)

fake_settler = Settler(0, "John Q Settler", {health:100, age:35, hunger:0, thirst:0}, {labor:1}, {food:0.1, water:0.1})

hunting_stand = Building(0, "Hunting Stand", "A stand for hunters to find food", {food:10}, {labor:2},{food:10})
food_silo = Building(1, "Food Silo", "A silo for storing food", {}, {}, {food:100})
water_tank = Building(2, "Water Tank", "A small tank of potable water", {}, {}, {water:100})