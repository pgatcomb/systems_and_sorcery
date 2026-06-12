/// Event struct.
use serde::{Serialize, Deserialize};
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct EventDef {
    pub id: u32,
    pub trigger_probability: f32,
    pub required_buildings: Vec<u32>,
    pub blocking_buildings: Vec<u32>,
    pub required_techs: Vec<u32>,
    pub blocking_techs: Vec<u32>,
    pub effects: Vec<EventEffect>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(tag = "type", content = "data")]
pub enum EventEffect {
    AdjustResource { resource_id: u32, amount: f32 },
    AdjustSettlerHealth { settler_id: u32, amount: i16 },
    AdjustBuildingHealth { building_id: u32, amount: f32 },
    DamageRandomBuilding { building_type: u32, amount: f32 },
    InjureRandomSettler { amount: i16 },
    TechProgress { amount: i16 },
    TechGained { tech_id: u32 },
    SettlerArrives {},
    SettlerLeaves {},
}
#[derive(Serialize, Deserialize, Clone)]
pub struct EventLog {
    pub event_id: u32,
    pub turn: u32,
}

impl Default for EventDef{
    fn default() -> EventDef{
        EventDef{
            id:0,
            trigger_probability:0.0,
            required_buildings:Vec::new(),
            blocking_buildings:Vec::new(),
            required_techs:Vec::new(),
            blocking_techs:Vec::new(),
            effects:Vec::new(),
        }
    }
}

impl EventDef{
    // Unusued, use From instead.
    fn _new(id:u32, trigger_probability:f32, required_buildings:Vec<u32>, blocking_buildings:Vec<u32>, required_techs:Vec<u32>, blocking_techs:Vec<u32>, effects:Vec<EventEffect>) -> EventDef{
        EventDef { id, trigger_probability, required_buildings, blocking_buildings, required_techs, blocking_techs, effects }
    }
}

#[test]
fn test_default_event(){
    let mut test_event:EventDef = EventDef::default();
    assert_eq!(test_event.id, 0);
    assert_eq!(test_event.trigger_probability, 0.0);
    test_event.effects.push(EventEffect::AdjustResource { resource_id: 0, amount: 1.0 });
    test_event.effects.push(EventEffect::SettlerLeaves {});
    for event in &test_event.effects{
        if let EventEffect::DamageRandomBuilding { building_type, amount } = event {
            assert_eq!(*building_type, 0);
            assert_eq!(*amount, 0.0);
        }
    }

}