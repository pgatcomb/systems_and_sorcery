use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Settler {
    pub id: u32,
    pub health: u8,
    pub age: u8,
    pub stamina: u8,
    pub build_skill: u8,
    pub work_skill: u8,
    pub research_skill: u8,
    pub affinity: Option<u32>,
    pub aversion: Option<u32>,
    mode: SettlerMode,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct SettlerInstance{
    pub id: u32,
    pub health: u8,
    pub stamina: u8,
    pub mode: SettlerMode,
    pub build_skill: u8,
    pub work_skill: u8,
    pub research_skill: u8,
    pub affinity: Option<u32>,
    pub aversion: Option<u32>,
}

impl From<&Settler> for SettlerInstance{
    fn from(settler_def:&Settler) -> Self{
        SettlerInstance { id: settler_def.id, health: settler_def.health, stamina: settler_def.stamina, mode: settler_def.mode,
        build_skill: settler_def.build_skill, work_skill: settler_def.work_skill, 
        research_skill: settler_def.research_skill, affinity: settler_def.affinity, aversion: settler_def.aversion }
    }
}

impl SettlerInstance{
    /// Apply a change of health, clamped by 0-100
    pub fn apply_health_change(&mut self, delta: i16) {
        let new = (self.health as i16 + delta).clamp(0, 100);
        self.health = new as u8;
    }
    /// Apply a change of stamina, clamped by 0-100
    pub fn apply_stamina_change(&mut self, delta: i16) {
    let new = (self.stamina as i16 + delta).clamp(0, 100);
    self.stamina = new as u8;
    }
    /// Depreciated, state is directly set in the engine Manually set the colonists mode
    pub fn _set_mode(&mut self, mode: SettlerMode) {
    self.mode = mode;
    }
    /// Depreciated, tested directly in the engine Can this settler/colonist work?
    pub fn _can_work(&self) -> bool{
        self.health > 0 && self.stamina > 0
    }
}

#[derive(Debug, PartialEq, Copy, Clone, Serialize, Deserialize)]
pub enum SettlerMode {
    Auto,
    Work,
    Construct,
    Research,
    Idle,
}

impl Default for Settler {
    /// Creates a default settler with 100 health/stamina and 50 of all other stats. No affinities
    fn default() -> Self {
        Settler {
            id: 0,
            health: 100,
            age: 50,
            stamina: 100,
            build_skill: 50,
            work_skill: 50,
            research_skill: 50,
            affinity: None,
            aversion: None,
            mode: SettlerMode::Auto,
        }
    }
}

impl Settler{
    pub fn new(id: u32, health: u8, age: u8, stamina: u8, build_skill: u8, work_skill: u8,research_skill: u8, affinity: Option<u32>, aversion: Option<u32>, mode:SettlerMode) -> Settler{
                Settler {id, health, age, stamina, build_skill, work_skill, research_skill, affinity, aversion, mode}
    }
}


#[test]
fn test_settler(){
    let settler = Settler::default();
    let mut test_settler = SettlerInstance::from(&settler);
      //println!("{:?}", test_settler);
    test_settler.apply_health_change(999);
    assert_eq!(test_settler.health, 100);
    test_settler.apply_health_change(-1000);
    assert_eq!(test_settler.health, 0);
    test_settler.apply_stamina_change(-9999);
    assert_eq!(test_settler.stamina, 0);
    assert!(!test_settler._can_work());
    test_settler.apply_health_change(100);
    test_settler.apply_stamina_change(100);
    assert!(test_settler._can_work());
    let new_mode:SettlerMode = SettlerMode::Idle;
    test_settler._set_mode(new_mode);
    assert_eq!(test_settler.mode, SettlerMode::Idle);
}