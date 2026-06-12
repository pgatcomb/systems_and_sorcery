//use crate::sim::settler::SettlerInstance;
use crate::sim::settler::{SettlerMode, SettlerInstance};
use crate::sim::building::BuildingInstance;
use crate::sim::resource::ResourceInstance;
use crate::sim::event::EventLog;
use crate::sim::tech::TechnologyState;
use crate::sim::definitions::Definitions;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;


impl Default for GameState{
    fn default() -> GameState{
        GameState {turn:0,
        settlers: HashMap::new(),
        buildings: Vec::new(),
        technologies: HashMap::new(),
        resources: HashMap::new(),
        build_queue: Vec::new(),
        research_queue: Vec::new(),
        events: Vec::new(),
        }
    }
}

impl GameState{
    pub fn new(defs: &Definitions) -> GameState{
        let turn:u32 = 0;
        let mut settlers = HashMap::new();
        for (id, citizen) in &defs.settler_defs{
            settlers.insert(*id, SettlerInstance::from(citizen));
        }
        let buildings = Vec::new();
        let technologies = HashMap::new();
        let mut resources = HashMap::new();
        // populate the resources with 0 values at the start
        for (id, resource) in &defs.resource_defs{
            resources.insert(*id, ResourceInstance::from(resource));
        }
        let build_queue = Vec::new();
        let research_queue = Vec::new();
        let events = Vec::new();
        GameState { turn, settlers, buildings, technologies, resources, build_queue, research_queue, events }
    }
}

#[derive(Serialize, Deserialize, Clone)]
pub struct GameState {
    pub turn: u32,
    pub settlers: HashMap<u32, SettlerInstance>,
    pub buildings: Vec<BuildingInstance>,
    pub technologies: HashMap<u32, TechnologyState>,
    pub resources: HashMap<u32,ResourceInstance>,
    pub build_queue: Vec<(u32, f32)>,  // (building_id, progress)
    pub research_queue: Vec<(u32, f32)>, // (research_id, progress)
    pub events: Vec<EventLog>,
}

#[derive(Serialize, Deserialize)]
pub enum CommandType {
    ColonistOrder { who: u32, assignment: SettlerMode },
    AddBuildToQueue{id: u32},
    OrderDemolish{id: u32},
    CancelBuilding{id: u32},
    AddResearch{id: u32},
    CancelResearch{id: u32},
}