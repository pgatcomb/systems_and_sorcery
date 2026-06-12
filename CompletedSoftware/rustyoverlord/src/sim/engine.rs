/*
Core settlement engine.  When triggered, this engine will process all the player commands and gamemaster commands and modify the settlement accordingly.  It will also trigger any events that need to be triggered based on the current state of the settlement.  
This engine is designed to be modular and can be easily extended with new features and mechanics as needed.
*/

//use std::process::Command;

use crate::sim::building::{BuildingInstance};
use crate::sim::gamestate::{GameState, CommandType};
use crate::sim::definitions::Definitions;
use crate::sim::tech::TechnologyState;
use crate::sim::settler::{SettlerMode, SettlerInstance};
use crate::sim::event::{EventEffect};

use std::collections::HashMap;
use rand::prelude::*;

//#[derive(Debug)]
struct WorkDemand{
    resource_work: HashMap<u32, f32>,
    build_work: f32,
    research_work: f32,
}

struct WorkAssignment{
    resource_work: HashMap<u32, f32>,
    build_work: f32,
    research_work: f32,
}


#[derive(Default)]
pub struct Engine {}

impl Engine {
    /// Unused
    pub fn _new() -> Engine{
        Engine {}
    }

    fn process_order(state: &mut GameState, defs: &Definitions, order: CommandType){
            match order{
                CommandType::ColonistOrder { who, assignment } => {                    
                    if let Some(citizen) = state.settlers.get_mut(&who) {
                        citizen.mode = assignment;
                        }
                    },
                CommandType::AddBuildToQueue { id } => {
                        if defs.building_defs.contains_key(&id) {
                            state.build_queue.push((id,0.0));
                            }
                    },
                CommandType::OrderDemolish { id } => {
                        if let Some(index) = state.buildings.iter().position(|x| x.id == id) {
                            state.buildings.swap_remove(index);
                            }
                    },
                CommandType::CancelBuilding { id } => {
                        if let Some(index) = state.build_queue.iter().position(|(x, _)|*x == id){
                            state.build_queue.swap_remove(index);
                        }
                    },
                CommandType::AddResearch { id } => {
                        if defs.technology_defs.contains_key(&id) {
                            state.research_queue.push((id,0.0));
                        }
                    },
                CommandType::CancelResearch { id } => {
                        if let Some(index) = state.research_queue.iter().position(|(x, _)| *x == id){
                            state.research_queue.swap_remove(index);
                        }
                    },
                //_ => unreachable!("Unknown type of colonist order issued!"),
                }
            }


    fn get_resource_work(state: &GameState, defs: &Definitions) -> HashMap<u32, f32> {
        let mut resource_work = HashMap::new();
        for building in &state.buildings {
            if let Some(details) = defs.building_defs.get(&building.id) {
                // Chain both iterators together to look like one clean loop
                let all_flows = details.outputs.iter().chain(details.inputs.iter());
                for (&resource, &amount) in all_flows {
                    *resource_work.entry(resource).or_insert(0.0) += amount;
                }
            }
        }
        resource_work
    }

    fn get_research_work(state: &GameState, defs: &Definitions) -> f32{
        let mut research_work:f32 = 0.0;
        for research in &state.research_queue{
            if let Some(details) = &defs.technology_defs.get(&research.0){
                research_work += details.research_time;
            }
        }
        research_work
    }

    fn get_build_work(state: &GameState, defs: &Definitions) -> f32{
        let mut build_work:f32 = 0.0;
        for building in &state.build_queue {
            if let Some(details) = &defs.building_defs.get(&building.0){
                build_work += details.build_time;
            }
        }
        build_work
    }

    fn get_work_contribution(settler: &SettlerInstance, remaining_work: &mut HashMap<u32, f32>) {
        let skill = settler.work_skill as f32;

        // 1. Try affinity first
        if let Some(resource) = settler.affinity {
            if let Some(work_available) = remaining_work.get_mut(&resource) {
                if *work_available > 0.0 {
                    let effective = 1.2 * skill;
                    let applied = effective.min(*work_available);
                    *work_available -= applied;
                    return;
                }
            }
        }

        // 2. Try any available work
        for (_resource, work_available) in remaining_work.iter_mut() {
            if *work_available > 0.0 {
                let effective = skill;
                let applied = effective.min(*work_available);
                *work_available -= applied;
                return;
            }
        }

        // 3. Try aversion (with penalty)
        if let Some(resource) = settler.aversion {
            if let Some(work_available) = remaining_work.get_mut(&resource) {
                if *work_available > 0.0 {
                    let effective = 0.5 * skill; // penalty
                    let applied = effective.min(*work_available);
                    *work_available -= applied;
                    return;
                }
            }
        }
    }

    fn get_construction_contribution(settler: &SettlerInstance, remaining_construction: &mut f32){
        if *remaining_construction > 0.0{
            let effective_build:f32 = settler.build_skill as f32;
            let applied = effective_build.min(*remaining_construction);
            *remaining_construction -= applied;
        }
    }

    fn get_research_contribution(settler: &SettlerInstance, remaining_research: &mut f32){
        if *remaining_research > 0.0{
            let effect_research_skill:f32 = settler.research_skill as f32;
            let applied:f32 = effect_research_skill.min(*remaining_research);
            *remaining_research -= applied;
        }
    }

    fn get_automatic_contribution(settler: &SettlerInstance, remaining_work: &mut HashMap<u32, f32>, remaining_research: &mut f32, remaining_construction: &mut f32){
        let any_work_left = remaining_work.values().any(|&value| value > 0.0);
        let any_construction_left = *remaining_construction > 0.0;
        let any_research_left = *remaining_research > 0.0;
        // we don't have to be so 'explicit' here, but I want to keep readability for priority high
        if any_work_left{
            Self::get_work_contribution(settler, remaining_work);
        }
        else if any_construction_left{
            Self::get_construction_contribution(settler, remaining_construction);
        }
        else if any_research_left{
            Self::get_research_contribution(settler, remaining_research);
        }
    }

    fn assign_settler_work(state: &GameState, work: WorkDemand) -> WorkAssignment{
        let mut remaining_work = work.resource_work.clone();
        let mut remaining_research = work.research_work;
        let mut remaining_construction = work.build_work;
        for settler in state.settlers.values(){
            // Either  dead or exhausted, no work possible!
            if settler.health == 0 || settler.stamina == 0{
                continue;
            }
            match settler.mode {
                SettlerMode::Idle => { continue },
                SettlerMode::Work => { Self::get_work_contribution(&settler, &mut remaining_work) },
                SettlerMode::Construct => { Self::get_construction_contribution(&settler, &mut remaining_construction) },
                SettlerMode::Research => { Self::get_research_contribution(&settler, &mut remaining_research) },
                SettlerMode::Auto => { Self::get_automatic_contribution(&settler, &mut remaining_work, &mut remaining_research, &mut remaining_construction) },
                }
        }
        let mut accomplished_work = HashMap::new();
        for (res_id, original_demand) in &work.resource_work {
            let left = remaining_work.get(res_id).unwrap_or(&0.0);
            accomplished_work.insert(*res_id, original_demand - left);
        }   

        WorkAssignment { resource_work: accomplished_work, build_work: work.build_work - remaining_construction, research_work: work.research_work - remaining_research }
    }

    fn manage_production(state: &mut GameState, defs: &Definitions, work_assignments: &mut WorkAssignment){ 
        // generate two empty hashmaps with our keys set and ready to go. We'll iterate through all our buildings to calculate what we produce and consume 
        let mut produced: HashMap<u32, f32> = HashMap::new();
        let mut consumed: HashMap<u32, f32> = HashMap::new();
        
        for building in &state.buildings{ 
            let building_def = &defs.building_defs.get(&building.id).unwrap(); 
            for (resource, amount) in &building_def.outputs{ 
                *produced.entry(*resource).or_insert(0.0) += amount; 
            } 
            for (resource, amount) in &building_def.inputs{ 
                *consumed.entry(*resource).or_insert(0.0) += amount; 
            } 
        } 

        // Apply modifiers based on actual available work

        for (resource_id, production) in produced.iter_mut() {
            if let Some(labor_available) = work_assignments.resource_work.get_mut(resource_id) {
                let labor_required = *production;

                if *labor_available > 0.0 && labor_required > 0.0 {
                    let efficiency = (*labor_available / labor_required).min(1.0);

                    *production *= efficiency;

                    if let Some(consumption) = consumed.get_mut(resource_id) {
                        *consumption *= efficiency;
                    }

                    let labor_used = labor_required * efficiency;
                    *labor_available -= labor_used;
                } else {
                    *production = 0.0;

                    if let Some(consumption) = consumed.get_mut(resource_id) {
                        *consumption = 0.0;
                    }
                }
            }
        }


        // Now we merge production with consumption and stockpile
        for (resource_id, resource) in &mut state.resources{
            let total_output = *produced.get(resource_id).unwrap_or(&0.0);
            let total_input = *consumed.get(resource_id).unwrap_or(&0.0);
            let current_stockpile = resource.amount as f32;
            let net = (current_stockpile + total_output) - total_input;
            if defs.resource_defs.get(resource_id).unwrap().flags.is_storable{
                resource.amount = net.max(0.0).round() as u32;
            }
        }


    }

    
    fn manage_research(state: &mut GameState,defs: &Definitions, work_available: &mut f32) {
        let mut i = 0;

        while i < state.research_queue.len() && *work_available > 0.0 {
            let (tech_id, progress) = &mut state.research_queue[i];
            let def = &defs.technology_defs[tech_id];

            let remaining = def.research_time - *progress;
            let applied = work_available.min(remaining);

            *progress += applied;
            *work_available -= applied;

            if *progress >= def.research_time {
                state.technologies.insert(
                    *tech_id,
                    TechnologyState {
                        id: *tech_id,
                        progress: def.research_time,
                        is_unlocked: true,
                    },
                );

                state.research_queue.swap_remove(i);
            } else {
                i += 1;
            }
        }
    }

    fn manage_construction(state: &mut GameState,defs: &Definitions,work_available: &mut f32) {
        let mut i = 0;

        while i < state.build_queue.len() && *work_available > 0.0 {
            let (building_id, progress) = &mut state.build_queue[i];
            let def = &defs.building_defs[building_id];

            let remaining = def.build_time - *progress;
            let applied = work_available.min(remaining);

            *progress += applied;
            *work_available -= applied;

            if *progress >= def.build_time {
                state.buildings.push(BuildingInstance {
                    id: *building_id,
                    progress: def.build_time,
                });

                state.build_queue.swap_remove(i);
            } else {
                i += 1;
            }
        }
    }

    fn manage_settlers(state: &mut GameState) {
        let food_available = state.resources.get(&3).unwrap().amount;   // Magic number alert
        let water_available = state.resources.get(&2).unwrap().amount;  // TODO make it a config option
        
        let total_food_needed = state.settlers.len() as u32;  
        let total_water_needed:u32 = (state.settlers.len() as f32 * 0.5).round() as u32;       

        if total_food_needed == 0 {
            return;  // no people, no food!
        }
        let food_efficiency: f32 = (food_available as f32 / total_food_needed as f32).clamp(0.0, 1.0);
        let water_efficiency: f32 = if total_water_needed == 0 { 1.0 } else {
            (water_available as f32 / total_water_needed as f32).clamp(0.0, 1.0)
        };

        for colonist in state.settlers.values_mut(){
            let health_change_from_water:i16= (-30.0 * (1.0 - water_efficiency)).round() as i16; // 30 damage to health if water is at 0
            colonist.apply_health_change(health_change_from_water);
            let health_change_from_food:i16 = (-10.0 * (1.0 - food_efficiency)).round() as i16; // 10 damage per tick from lack of food
            colonist.apply_health_change(health_change_from_food);

            // Simple stamina calculation for now. If they're healthy, their fine, otherwise they start 'feeling it'
            if colonist.mode == SettlerMode::Idle {
                colonist.apply_stamina_change(20);
            }
            else{
                if colonist.health <= 50 {
                    colonist.apply_stamina_change(-10);
                }
            }

        }

        // Remove food from resources
        if let Some(food_resource) = state.resources.get_mut(&3) {
                    let food_consumed = (total_food_needed as f32 * food_efficiency).round() as u32;
                    food_resource.amount = food_resource.amount.saturating_sub(food_consumed);
                }

        // Remove water from resources
        if let Some(water_resource) = state.resources.get_mut(&2) {
            let water_consumed = (total_water_needed as f32 * water_efficiency).round() as u32;
            water_resource.amount = water_resource.amount.saturating_sub(water_consumed);
        }
    }

    /// Manage Storage consists of calculating total storage of the colony then adjusting the stockpile.  Anything that
    /// cannot be stored results in the stockpile value being dropped to zero.
    fn manage_storage(state: &mut GameState, defs: &Definitions){
        let mut resource_storage = HashMap::new();
        
        // Get total storage available.
        for building in &state.buildings {
            if let Some(details) = defs.building_defs.get(&building.id) {
                for (&resource, &amount) in &details.storage_capacity {
                    *resource_storage.entry(resource).or_insert(0) += amount as u32;
                }
            }
        }
        for (id, resource) in &mut state.resources {
            let storable: bool = defs.resource_defs.get(&id).unwrap().flags.is_storable;
            
            if !storable {
                resource.amount = 0; // Works now
                continue;
            }
            let max_storage = *resource_storage.get(id).unwrap_or(&0) as u32;
            resource.amount = resource.amount.min(max_storage);
        }
    }

    fn handle_events(state: &mut GameState, defs: &Definitions){
        // The reason we're takine a mutable is since the the events themselves can cause things to change in the game state!
        let mut rng = rand::rng();
        for (_id, event) in &defs.event_defs{
            let roll:f32 = rng.random_range(0.0..=1.0);
            if roll <= event.trigger_probability{
                println!("Eventid: {} can fire", &event.id);

                // Check to see if we have a building that prevents the event
                let is_blocked = event.blocking_buildings.iter().any(|&id| {
                    state.buildings.iter().any(|building| building.id ==id)
                });
                if is_blocked { continue };

                // Now check to see if we have a tech that prevents the event
                let is_blocked = event.blocking_techs.iter().any(|id| {
                    state.technologies.contains_key(id)
                });
                if is_blocked {continue};

                // Now see if we have the required building to do it, if we don't no issue
                let required_build = event.required_buildings.iter().any(|&id|{
                    state.buildings.iter().any(|building| building.id == id)
                });

                if !required_build { continue };

                let required_tech = event.required_techs.iter().any(|id| {
                    state.technologies.contains_key(id)
                });

                if !required_tech { continue };
                // If we reached this line, we can actually do the event
                for effect in &event.effects{
                    match effect {
                        EventEffect::AdjustResource { resource_id, amount} => {println!("Resource {} changed by {}", resource_id, amount);},
                        EventEffect::AdjustSettlerHealth { settler_id, amount} => {println!("Settler {} health changed by {}", settler_id, amount);},
                        EventEffect::AdjustBuildingHealth { building_id, amount} => {println!("Building {} health changed by {}", building_id, amount);},
                        EventEffect::DamageRandomBuilding { building_type, amount } => {println!("Buildng {} was damaged by {}", building_type, amount);},
                        EventEffect::InjureRandomSettler { amount } => {println!("Random settler injured by {}", amount);},
                        EventEffect::TechProgress { amount } => {println!("Random tech made {} progress", amount);},
                        EventEffect::TechGained { tech_id } => {println!("New tech: {} learned!", tech_id);},
                        EventEffect::SettlerArrives {  } => {},
                        EventEffect::SettlerLeaves {  } => {},
                    }
                }

            }
        }
    }

    pub fn run_turn(state: &mut GameState, defs: &Definitions, command_queue: Vec<CommandType>){
        println!("Advancing from turn {} to {}", state.turn, state.turn + 1);
        state.turn += 1;
        // Step 1: Process the incoming orders
        for order in command_queue{
            Self::process_order(state, &defs, order);
        }
        // Step 2: Calculate the total demand for all types of work.
        let resource_work:HashMap<u32, f32> = Self::get_resource_work(&state, &defs);
        let research_work:f32 = Self::get_research_work(&state, &defs);
        let build_work:f32 = Self::get_build_work(&state, &defs);
        let work_required = WorkDemand{resource_work, build_work, research_work};
        // Step 3: Iterate through the settlers one at a time to determine what work they need to do, calculate the total work 'accomplishable'
        let mut work_assignments = Self::assign_settler_work(&state, work_required);
        // Step 4: Iterate through all buildings to determine what is produced and consumed from/to our stockpile. This will be modified by the work available
        // Step 4.1 Calculate all productions
        // Step 4.2 Calculate all consumption
        // Step 4.3 Final stockpile = Production + Previous Stockpile - consumption
        Self::manage_production(state, defs, &mut work_assignments);    
        // Step 5: Apply construction
        Self::manage_construction(state, defs, &mut work_assignments.build_work);
        // Step 6: Apply research
        Self::manage_research(state, defs, &mut work_assignments.research_work);
        // Step 7: Iterate through our colonists once more to modify their respective stats, e.g. not enough food, water, etc.
        Self::manage_settlers(state);
        // Step 8: Calculate available storage and update our gamestate with the new amounts in the stockpiles
        Self::manage_storage(state, &defs);
        // Step 9: Handle events
        Self::handle_events(state, &defs);
        // Step 10: At this time, gamestate is updated with everything that's new :)
        return;  //Totally unecessary but for some reason it feels natural
    }
}


#[test]
fn test_engine_advances_turn() {
    let defs = Definitions::default();
    let mut state = GameState::new(&defs);
    let command_queue = Vec::new();
    Engine::run_turn(&mut state, &defs, command_queue);
    assert_eq!(state.turn, 1);
}
