use dndbattlesim::*;
use std::env;


struct SimulationParameter{
    monster_data_path: String,
    team1_path: String,
    team2_path: String,
    num_simulations: u32,
}
impl SimulationParameter{
    fn new() -> Self{
        let args: Vec<String> = env::args().collect();
        for item in &args{
            println!("{}", item);
        }

        SimulationParameter{
            monster_data_path: args[1].clone(),
            team1_path: args[2].clone(),
            team2_path: args[3].clone(),
            num_simulations: args[4].parse().unwrap(),
        }
        }
}

fn main() {
    // Get command line arguments
    let sim_details:SimulationParameter = SimulationParameter::new();
    let monster_templates_filename = sim_details.monster_data_path;
    let team1_filename = sim_details.team1_path;
    let team2_filename = sim_details.team2_path;
    let number_engagements = sim_details.num_simulations;
    let monster_templates = load_csv_directly_to_templates(&monster_templates_filename);
    println!("Number of combatants recorded: {}", monster_templates.len());
    let team1_file = load_team(&team1_filename);
    let team2_file = load_team(&team2_filename);
    let mut team1 = create_combatants(&team1_file, &monster_templates);
    let mut team2 = create_combatants(&team2_file, &monster_templates);
    // Smoke Test
    println!("Team 1: {}", team1.get_summary());
    println!("Team 2: {}", team2.get_summary());
    let mut team_1_wins = 0;
    let mut team_2_wins = 0;
    for engagement in 0..number_engagements
    {
        while team1.is_any_alive() && team2.is_any_alive()
        {
            if engagement % 2 == 0
            {
                for team_member in team1.get_alive_combatants()
                {
                    let target = match team2.get_random_target_mut(){
                        Some(target) => target,
                        None => break,
                    };
                    if team_member.roll_check(target.get_ac())
                    {
                        let damage = team_member.roll_damage();
                        target.take_damage(damage);
                    }
                }
                for team_member in team2.get_alive_combatants()
                {
                    let target = match team1.get_random_target_mut(){
                        Some(target) => target,
                        None => break,
                    };
                    if team_member.roll_check(target.get_ac())
                    {
                        let damage:i32 = team_member.roll_damage();
                        target.take_damage(damage);
                    }
                }
            }
            else 
            {
                for team_member in team2.get_alive_combatants()
                {
                    let target = match team1.get_random_target_mut(){
                        Some(target) => target,
                        None => break,
                    };
                    if team_member.roll_check(target.get_ac())
                    {
                        let damage:i32 = team_member.roll_damage();
                        target.take_damage(damage);
                    }
                }
                for team_member in team1.get_alive_combatants()
                {
                    let target = match team2.get_random_target_mut(){
                        Some(target) => target,
                        None => break,
                    };
                    if team_member.roll_check(target.get_ac())
                    {
                        let damage = team_member.roll_damage();
                        target.take_damage(damage);
                    }
                }
                
            }
        }
        if team1.is_any_alive()
        {
            team_1_wins += 1;
        }
        else
        {
            team_2_wins += 1;
        }
        team1.reset_hp(&monster_templates);
        team2.reset_hp(&monster_templates);
    }
    println!("Final report");
    println!("Team 1 wins: {}", team_1_wins);
    println!("Team 2 wins: {}", team_2_wins);
}