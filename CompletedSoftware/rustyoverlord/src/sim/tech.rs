use serde::{Deserialize, Serialize};

/// A technology consists of a uniqueid, a list of no more than four prerequisites and a reseaerch time consisting of a float representing
/// The number of 'days' or 'ticks' it takes to complete.
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct TechnologyDef {
    pub id: u32,
    pub prerequisites: [u32; 4],
    pub research_time: f32,
}

impl TechnologyDef {
    pub fn new(id:u32, prerequisites:[u32; 4], research_time: f32) -> TechnologyDef {
        TechnologyDef {id, prerequisites, research_time}
    }
    pub fn default() -> TechnologyDef{
        TechnologyDef { id: 0, prerequisites: [0,0,0,0], research_time: 1.0 }
    }
    pub fn _describe(&self) -> String{
        format!("{} {:?} {}", self.id, self.prerequisites, self.research_time)
    }
}

/// TechnologyState represents an actual researched (or being researched) tech. at 1.0 progress it is unlocked permanently.
#[derive(Serialize, Deserialize, Clone)]
pub struct TechnologyState {
    pub id: u32,
    pub progress: f32,
    pub is_unlocked: bool,
}

impl Default for TechnologyState{
    fn default() -> TechnologyState {
        TechnologyState { id: 0, progress: 0.0, is_unlocked: false }
    }
}

impl TechnologyState {
    // Depreciated, use From
    pub fn _new(id: u32, progress:f32, is_unlocked:bool) -> TechnologyState{
        TechnologyState{id,progress,is_unlocked}
    }
    // Depreciated, we use a hashmap to determine progress of the tech
    pub fn _update_progress(&mut self, progress:f32){
        self.progress += progress;
        if self.progress >= 1.0{
            self.progress = 1.0;
            self.is_unlocked = true;
        }
        else if self.progress <=0.0 {
            self.progress = 0.0;
            // We do NOT change the is_unlocked status if our progress somehow is reduced to 0.0
        }
    }
}

/// Convert a technology definition into a technology state with 0 progress and unlocked false
impl From<&TechnologyDef> for TechnologyState {
    fn from(techdef:&TechnologyDef) -> Self{
        TechnologyState { id:techdef.id, progress: 0.0, is_unlocked: false }
    }
}

#[test]
fn test_default_tech_def(){
    let test_tech_def:TechnologyDef = TechnologyDef::default();
    assert_eq!(test_tech_def.id, 0);
    assert!(test_tech_def.prerequisites.iter().all(|&x| x==0));
    assert_eq!(test_tech_def.research_time, 1.0);
}

#[test]
fn test_tech_def_to_state(){
    let test_tech_def:TechnologyDef = TechnologyDef::default();
    let test_tech_state:TechnologyState = TechnologyState::from(&test_tech_def);
    assert_eq!(test_tech_state.id, 0);
    assert_eq!(test_tech_state.progress, 0.0);
    assert!(!test_tech_state.is_unlocked);
}

#[test]
fn test_tech_state_methods(){
    let mut test_tech_state:TechnologyState = TechnologyState::default();
    test_tech_state._update_progress(0.1);
    assert_eq!(test_tech_state.progress, 0.1);
    test_tech_state._update_progress(5.0);
    assert_eq!(test_tech_state.progress, 1.0);
    assert!(test_tech_state.is_unlocked);
    test_tech_state._update_progress(-10.0);
    assert_eq!(test_tech_state.progress, 0.0);
    assert!(test_tech_state.is_unlocked); // If a tech is unlocked, it's unlocked. Period.  You can't un-unlock a tech.
}