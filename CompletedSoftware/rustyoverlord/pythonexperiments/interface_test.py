from rich.console import Console
from rich.table import Table
from pydantic.dataclasses import dataclass
import csv

console = Console()
citizens = []

@dataclass
class Citizen:
    name:str
    age:int
    health:int
    research_skill:int
    work_skill:int
    construction_skill:int
    resource_affinity:str
    resoruce_aversion:str
        

def load_csv(filename):
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            name = row['name']
            age = row['age']
            health = row['health']
            research_skill = row['research_skill']
            work_skill = row['work_skill']
            construction_skill = row['construction_skill']
            resource_affinity = row['resource_affinity']
            resource_aversion = row['resource_aversion']
            citizens.append(Citizen(name,age,health,research_skill,work_skill,construction_skill,resource_affinity,resource_aversion))


def pp(value:int) -> str:
    if value >= 85:
        return f"[bold green]{value}[/bold green]"
    elif value >= 70:
        return f"[green]{value}[green]"
    elif value >=50:
        return f"[cyan]{value}[/cyan]"
    elif value >=35:
        return f"[blue]{value}[/blue]"
    else:
        return f"[red]{value}[/red]"

load_csv("citizens.csv")
print(f"{len(citizens)} citizens loaded.")


table = Table("Name", "Age", "Health", "Research Skill", "Work Skill",
         "Construction Skill", "Affinity", "Aversion", title="Citizens")

for citizen in citizens:
    name = citizen.name
    age = str(citizen.age)
    health = pp(citizen.health)
    research_skill = pp(citizen.research_skill)
    work_skill = pp(citizen.work_skill)
    construction_skill = pp(citizen.construction_skill)
    affinity = citizen.resource_affinity
    aversion = citizen.resoruce_aversion
    table.add_row(name,age,health,research_skill,work_skill,construction_skill,affinity,aversion)
    
console.print(table)