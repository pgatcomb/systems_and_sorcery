use crate::sim::settler::{Settler};
use crate::sim::building::BuildingDef;
use crate::sim::resource::ResourceDef;
use crate::sim::event::EventDef;
use crate::sim::tech::TechnologyDef;
use crate::sim::event::EventEffect;

use std::collections::HashMap;
use serde::{Serialize, Deserialize};


#[derive(Serialize, Deserialize, Clone)]
pub struct Definitions{
    pub settler_defs:HashMap<u32, Settler>,
    pub building_defs:HashMap<u32, BuildingDef>,
    pub technology_defs:HashMap<u32, TechnologyDef>,
    pub resource_defs:HashMap<u32, ResourceDef>,
    pub event_defs:HashMap<u32, EventDef>,
}

impl Definitions {
    pub fn new(settler_defs:HashMap<u32, Settler>, 
        building_defs:HashMap<u32, BuildingDef>,    
        technology_defs:HashMap<u32, TechnologyDef>,
        resource_defs:HashMap<u32, ResourceDef>,
        event_defs:HashMap<u32, EventDef>) -> Definitions {
            Definitions { settler_defs, building_defs, technology_defs, resource_defs, event_defs }
        }
    /// Validate buildings, ensuring that they have appropriate inputs, outputs, storages, etc.
    pub fn validate_buildings(&self, errors: &mut Vec<String>) {
    for (id, building) in &self.building_defs {
        for res_id in building.inputs.keys() {
            if !self.resource_defs.contains_key(res_id) {
                errors.push(format!(
                    "Building {} has invalid input resource {}",
                    id, res_id
                ));
            }
        for res_id in building.outputs.keys() {
            if !self.resource_defs.contains_key(res_id) {
                errors.push(format!(
                    "Building {} has invalid output resource {}",
                    id, res_id
                ));
            }
        }
        for res_id in building.storage_capacity.keys() {
            if !self.resource_defs.contains_key(res_id) {
                errors.push(format!(
                    "Building {} has invalid storage {}",
                    id, res_id
                ));
            }
            else if !self.resource_defs.get(res_id).unwrap().flags.is_storable {
                errors.push(format!("Building {} has a resource {} that cannot be stored", id, res_id));
            }

        }
    }
    }
}
    /// Validate settler details such as health, stamina, age, etc.
    pub fn validate_settlers(&self, errors: &mut Vec<String>) {
        for (id, settler) in &self.settler_defs{
                if !(0..=100).contains(&settler.health){
                    errors.push(format!("Settler id: {} has a health value of {}", id, &settler.health));
                }
                if !(0..=100).contains(&settler.stamina){
                    errors.push(format!("Settler id: {} has a stamina value of {}", id, &settler.stamina));
                }
                if !(0..=100).contains(&settler.build_skill){
                    errors.push(format!("Settler id: {} has a build skill value of {}", id, &settler.build_skill));
                }
                if !(0..=100).contains(&settler.work_skill){
                    errors.push(format!("Settler id: {} has a work skill value of {}", id, &settler.work_skill));
                }
                if !(0..=100).contains(&settler.research_skill){
                    errors.push(format!("Settler id: {} has a research value of {}", id, &settler.research_skill));
                }
                if !self.resource_defs.contains_key(&settler.affinity.unwrap_or_default()){
                    errors.push(format!("Settler id: {} has an affinity problem with resource id: {}", id, &settler.affinity.unwrap_or_default()));
                }
                if !self.resource_defs.contains_key(&settler.aversion.unwrap_or_default()){
                    errors.push(format!("Settler id: {} has an aversion problem with resource id: {}", id, &settler.affinity.unwrap_or_default()));
                }
            } 
        }

    /// Tech Validator
    pub fn validate_techs(&self, errors: &mut Vec<String>){
        for (id, tech) in &self.technology_defs{
            if tech.research_time < 0.0 {
                errors.push(format!("Tech id: {} has a negative research time", id));
            }
            for preq in tech.prerequisites{
                if !&self.technology_defs.contains_key(&preq) {
                    errors.push(format!("Tech id: {} has an invalid prerequisite id {}", id, preq));
                }
            }
        }
    }
    /// Event validator
    pub fn validate_events(&self, errors: &mut Vec<String>){
        for (id, event) in &self.event_defs{
            if event.trigger_probability < 0.0 || event.trigger_probability > 1.0{
                errors.push(format!("Event id {} has a trigger probability: {} out of range", id, event.trigger_probability));
            }
            for item in &event.blocking_buildings{
                if !self.building_defs.contains_key(item){
                    errors.push(format!("Event id: {} contains an invalid blocking building id {}", id, item));
                }
            }
            for item in &event.required_buildings{
                if !self.building_defs.contains_key(item){
                    errors.push(format!("Event id: {} contains an invalid required building id {}", id, item));
                }
            }
            for item in &event.blocking_techs{
                if !self.technology_defs.contains_key(item){
                    errors.push(format!("Event id: {} contains an invalid blocking tech id {}", id, item));
                }
            }
            for item in &event.required_techs{
                if !self.technology_defs.contains_key(item){
                    errors.push(format!("Event id: {} contains an invalid required tech id {}", id, item));
                }
            }
            self.validate_event_effects(id, event, errors);
        }
    }

    /// Event effects validator    
    pub fn validate_event_effects(&self,event_id: &u32,event: &EventDef,errors: &mut Vec<String>) {
        for effect in &event.effects {
            match effect {
                EventEffect::AdjustResource { resource_id, amount } => {
                    if !self.resource_defs.contains_key(resource_id) {
                        errors.push(format!("Event {} → AdjustResource uses invalid resource {}",event_id, resource_id));
                    }
                    if *amount == 0.0 {
                        errors.push(format!(
                            "Event {} → AdjustResource has zero amount",
                            event_id
                        ));
                    }
                }
                EventEffect::AdjustSettlerHealth { settler_id, amount } => {
                    if *amount == 0 {
                        errors.push(format!("Event {} → AdjustSettlerHealth has zero change",event_id));
                    }
                    if !self.settler_defs.contains_key(settler_id){
                        errors.push(format!("Event {} affects a non_existent settler {}", event_id, settler_id));
                    }
                }

                EventEffect::AdjustBuildingHealth { building_id, amount } => {
                    if !self.building_defs.contains_key(building_id) {
                        errors.push(format!("Event {} AdjustBuildingHealth invalid building {}",event_id, building_id));
                    }
                    if *amount < 0.0 || *amount > 1.0{
                        errors.push(format!("Event {} AdjustBuildingHealth of range {} is out of range for a health adjustment", event_id, amount));
                    }
                }

                EventEffect::DamageRandomBuilding { building_type, amount } => {
                    if !self.building_defs.contains_key(building_type) {
                        errors.push(format!( "Event {} → invalid building type {} for random damage",event_id, building_type));
                    }

                    if *amount <= 0.0 {
                        errors.push(format!("Event {} → DamageRandomBuilding must have positive amount",event_id));
                    }
                }

                EventEffect::InjureRandomSettler { amount } => {
                    if *amount <= 0 {
                        errors.push(format!("Event {} → InjureRandomSettler must be positive",event_id));
                    }
                }

                EventEffect::TechProgress { amount } => {
                    if *amount == 0 {
                        errors.push(format!("Event {} → TechProgress has zero effect",event_id));
                    }
                }

                EventEffect::TechGained { tech_id } => {
                    if !self.technology_defs.contains_key(tech_id) {errors.push(format!("Event {} → invalid tech gained {}",event_id, tech_id));
                    }
                }

                EventEffect::SettlerArrives {} => {
                    // always valid
                }

                EventEffect::SettlerLeaves {} => {
                    // always valid
                }
            }
        }
    }




}


impl Default for Definitions{
    fn default() -> Definitions{
        let mut settler_defs = HashMap::new();
        let mut building_defs = HashMap::new();
        let mut technology_defs = HashMap::new();
        let mut resource_defs = HashMap::new();
        let mut event_defs = HashMap::new();

        // Initialize default settlers (10 basic ones)
        for id in 0..10 {
            let mut default_settler = Settler::default();
            default_settler.id = id;
            settler_defs.insert(id, default_settler);

            let mut default_building = BuildingDef::default();
            default_building.id = id;
            building_defs.insert(id, default_building);

            let mut default_technology = TechnologyDef::default();
            default_technology.id = id;
            technology_defs.insert(id, default_technology);

            let mut default_resource = ResourceDef::default();
            default_resource.id = id;
            resource_defs.insert(id, default_resource);

            let mut default_event = EventDef::default();
            default_event.id = id;
            default_event.trigger_probability = id as f32 * 0.1;  // Each event is slightly more likely than the previous in the default
            event_defs.insert(id, default_event);
        }

        Definitions {
            settler_defs,
            building_defs,
            technology_defs,
            resource_defs,
            event_defs,
          }
    }
}

#[test]
fn test_default_definitions()
{
    let default_defs = Definitions::default();
    assert_eq!(default_defs.settler_defs.len(), 10);
    assert_eq!(default_defs.building_defs.len(), 10);
    assert_eq!(default_defs.technology_defs.len(), 10);
    assert_eq!(default_defs.resource_defs.len(), 10);

}