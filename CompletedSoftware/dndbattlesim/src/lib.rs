use rand::Rng;
use serde::Deserialize;
use rayon::prelude::*;


#[derive(Clone)]
pub struct DiceRoll {
    number_of_dice: u32,
    die_sides: u32,
    modifier: i32,
}

impl DiceRoll{
    pub fn roll(&self) -> i32{
        let mut total = 0;
        let mut rng = rand::thread_rng();
        for _i in 0..self.number_of_dice{
            let random_number = rng.gen_range(1..=self.die_sides) as i32; 
            total += random_number;
        }
        total + self.modifier
    }
}

pub fn parse_dice(input: &str) -> Result<DiceRoll, String> {
    // Split at 'd'
    let (num_str, rest) = input
        .split_once('d')
        .ok_or("Missing 'd' in dice expression")?;

    let number_of_dice = num_str
        .parse::<u32>()
        .map_err(|_| "Invalid number of dice")?;

    // Look for + or -
    let (sides_str, modifier) = if let Some(idx) = rest.find(['+', '-']) {
        let sides = rest[..idx]
            .parse::<u32>()
            .map_err(|_| "Invalid number of sides")?;

        let modifier = rest[idx..]
            .parse::<i32>()
            .map_err(|_| "Invalid modifier")?;

        (sides, modifier)
    } else {
        // No modifier
        let sides = rest
            .parse::<u32>()
            .map_err(|_| "Invalid number of sides")?;

        (sides, 0)
    };

    Ok(DiceRoll {
        number_of_dice,
        die_sides: sides_str,
        modifier,
    })
}


//monster_name,hp,ac,attack_bonus,damage,challenge_rating,flags
#[derive(Debug, Deserialize)]
pub struct Record{
    monster_name: String,
    hp: u32,
    ac: u32,
    attack_bonus: u32,
    damage: String,
    flags: String,
}

#[derive(Clone)]
pub struct MonsterTemplate {
    name: String,
    hp: i32,
    ac: u32,
    attack_roll: DiceRoll,
    damage_roll: DiceRoll,
    flags: String,
}
impl MonsterTemplate {
    pub fn instantiate(&self) -> Combatant {
        Combatant {
            name: self.name.clone(),
            hp: self.hp,
            ac: self.ac,
            attack_roll: self.attack_roll.clone(),
            damage_roll: self.damage_roll.clone(),
            flags: self.flags.clone(),
        }
    }
}

#[derive(Clone)]
pub struct Combatant{
    name: String,
    hp: i32,
    ac: u32,
    attack_roll: DiceRoll,
    damage_roll: DiceRoll,
    flags: String,
}
impl Combatant{
    pub fn get_summary(&self) -> String{
        let return_string: String = format!("{}. HP: {} AC: {} Attack Roll: {}D{}+{} Damage Roll: {}D{}+{}\n Flags: {}", self.name, self.hp, self.ac, self.attack_roll.number_of_dice,self.attack_roll.die_sides, self.attack_roll.modifier, self.damage_roll.number_of_dice, self.damage_roll.die_sides, self.damage_roll.modifier, self.flags);
        return_string
    }

    pub fn get_ac(&self) -> i32{
        self.ac as i32
    }

    pub fn roll_check(&self, target_number: i32) -> bool{
        let attack_roll = self.attack_roll.roll();
        attack_roll >= target_number
    }

    pub fn roll_damage(&self) -> i32{
        self.damage_roll.roll()

    }

    pub fn is_alive(&self) -> bool{
        self.hp > 0
    }

    pub fn take_damage(&mut self, damage: i32) {
        if damage <= 0{
            return;
        }
        else{
        self.hp -= damage;
        if self.hp < 0{
            self.hp = 0;
        }
        }
        
    }
}

#[derive(Clone)]
pub struct Team {
    pub name: String,
    pub combatants: Vec<Combatant>,
}

impl Team {
    pub fn new(name: String, combatants: Vec<Combatant>) -> Self {
        Team { name, combatants }
    }

    /// Returns a summary string of the team and its combatants.
    pub fn get_summary(&self) -> String {
        let mut summary = format!("Team: {}\n", self.name);
        for combatant in &self.combatants {
            summary.push_str(&format!("  - {}\n", combatant.get_summary()));
        }
        summary
    }

    /// Checks if any combatant in the team is still alive.
    pub fn is_any_alive(&self) -> bool {
        self.combatants.par_iter().any(|c| c.is_alive())
    }

    /// Returns a vector of mutable references to combatants that are currently alive.
    pub fn get_alive_combatants_mut(&mut self) -> Vec<&mut Combatant> {
        self.combatants.par_iter_mut().filter(|c| c.is_alive()).collect()
    }

    /// Returns a vector of immutable references to combatants that are currently alive.
    pub fn get_alive_combatants(&self) -> Vec<&Combatant> {
        self.combatants.par_iter().filter(|c| c.is_alive()).collect()
    }

    /// Resets the HP of all combatants in the team to their initial values based on templates.
    pub fn reset_hp(&mut self, templates: &[MonsterTemplate]) {
        for combatant in &mut self.combatants {
            if let Some(template) = templates.iter().find(|t| t.name == combatant.name) {
                combatant.hp = template.hp;
            }
        }
    }

    /// Selects and returns a mutable reference to a random alive combatant from the team, if any.
    pub fn get_random_target_mut(&mut self) -> Option<&mut Combatant> {
        let mut alive_combatants: Vec<&mut Combatant> = self.combatants.par_iter_mut().filter(|c| c.is_alive()).collect();
        if alive_combatants.is_empty() {
            None
        } else {
            let mut rng = rand::thread_rng();
            let index = rng.gen_range(0..alive_combatants.len());
            Some(alive_combatants.remove(index))
        }
    }
}

impl From<Record> for MonsterTemplate {
    fn from(r: Record) -> Self {
        let attack_roll = parse_dice(&format!("1d20+{}", r.attack_bonus)).unwrap();
        let damage_roll = parse_dice(&r.damage).unwrap();

        MonsterTemplate {
            name: r.monster_name,
            hp: r.hp as i32,
            ac: r.ac,
            attack_roll,
            damage_roll,
            flags: r.flags,
        }
    }
}

#[derive(Debug, Deserialize)]
pub struct TeamFile {
    pub team_name: String,
    pub members: Vec<String>,
}

pub fn load_csv_directly_to_templates(filename: &str) -> Vec<MonsterTemplate> {
    let mut reader = csv::Reader::from_path(filename).unwrap();
    reader.deserialize::<Record>()
    .map(|result| {
        let record = result.unwrap();
        MonsterTemplate::from(record)
    })    
    .collect()
}


pub fn load_team(path: &str) -> TeamFile {
    let text = std::fs::read_to_string(path).unwrap();
    serde_json::from_str(&text).unwrap()
}

/// Creates a `Team` from a `TeamFile` and a list of `MonsterTemplate`s.
pub fn create_combatants(team_file: &TeamFile, templates: &[MonsterTemplate]) -> Team {
    let combatants = team_file.members
        .par_iter()
        .filter_map(|member_name| {
            templates
                .iter()
                .find(|t| t.name == *member_name)
                .map(|template| template.instantiate())
        }).collect();
    Team::new(team_file.team_name.clone(), combatants)
}

#[test]
fn run_tests() -> Result<(), String> 
{
    println!("Checking the operation of the fields.");
    let test_dice = DiceRoll {
        number_of_dice: 2,
        die_sides: 6,
        modifier: 1,
    };
    println!("The test roll is {}", test_dice.roll());

    println!("Testing the combatant struct");
    let test_combatant = Combatant {
        name: String::from("Test Monster"),
        hp: 15,
        ac: 14,
        attack_roll: DiceRoll {
            number_of_dice: 1,
            die_sides: 20,
            modifier: 3,
        },
        damage_roll: DiceRoll {
            number_of_dice: 1,
            die_sides: 8,
            modifier: 2,
        },
        flags: String::from("TestMonster"),
        };
    println!("{}", test_combatant.get_summary());
    let test_attack = test_combatant.roll_check(1);
    println!("Test attack roll result {}", test_attack);
    let test_damage_roll = test_combatant.roll_damage();
    println!("The damage roll was {}", test_damage_roll);
    println!("Testing the record reading struct");
    let test_record = Record {
        monster_name: String::from("Test Monster"),
        hp: 15,
        ac: 14,
        attack_bonus: 3,
        damage: String::from("1d8+2"),
        flags: String::from("TestMonster"),
        };
        println!("{:?}", test_record);

    let mut test_team1 = Team::new("Test Team 1".to_string(), vec![test_combatant.clone(), test_combatant.clone()]);
    println!("{}", test_team1.get_summary());
    let mut test_team2: Team = Team::new("Test Team 2".to_string(), vec![test_combatant.clone(), test_combatant.clone()]);
    println!("{}", test_team2.get_summary());
    match test_team1.is_any_alive(){
        true => println!("Team 1 is alive"),
        false => println!("Team 1 is dead"),
    };
    match test_team2.is_any_alive(){
        true => println!("Team 2 is alive"),
        false => println!("Team 2 is dead"),
    };

    for team_member in &mut test_team1.get_alive_combatants_mut(){
        team_member.take_damage(999);
        println!("{}",  team_member.get_summary());
    }
    println!("{}", test_team1.is_any_alive());
    for team_member in test_team2.get_alive_combatants(){
        println!("{}",  team_member.get_summary());
    }
    
    let random_target = test_team2.get_random_target_mut();
    println!("Random target is {}", random_target.unwrap().get_summary());
    


    Ok(())
}

