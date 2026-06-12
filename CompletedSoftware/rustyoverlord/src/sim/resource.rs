use serde::{Deserialize, Serialize};

/// A resource is defined as a unique id and flags
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ResourceDef {
    pub id: u32,
    pub flags: ResourceFlags,
}

impl ResourceDef{
    pub fn new(id: u32, flags: ResourceFlags) -> ResourceDef{
        ResourceDef { id, flags }
    }

    pub fn default() -> ResourceDef{
        let default_flags = ResourceFlags::default();
        ResourceDef {id:0, flags:default_flags}
    }
    
    // Used for debugging only
    pub fn _describe(&self) -> String{
        format!("Resource: {}, {:?}", self.id, self.flags)
    }

}

/// An instance is simply the id itself as a wrapper for handling
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ResourceInstance {
    pub id: u32,
    pub amount: u32,
}

impl ResourceInstance {
    /// Depreciated, use from
    pub fn _new(id:u32, amount: u32) -> ResourceInstance{
        ResourceInstance { id , amount}
    }
    /// Depreciated, use from
    pub fn _default() -> ResourceInstance{
        ResourceInstance { id: 0 , amount: 0}
    }
}

/// Represents the logic of a resource in an expandable set of flags/logic
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ResourceFlags {
    pub is_roleplay: bool,
    pub is_storable: bool,
}

impl Default for ResourceFlags{
    fn default() -> ResourceFlags{
        ResourceFlags{is_roleplay:false, is_storable:true}
    }
}

impl ResourceFlags {
    pub fn new(is_roleplay:bool, is_storable:bool) -> ResourceFlags{
        ResourceFlags{is_roleplay, is_storable}
    }

}

impl From<&ResourceDef> for ResourceInstance{
    fn from(resource_def:&ResourceDef) -> Self{
        ResourceInstance { id:resource_def.id, amount: 0}
    }
}

#[test]
fn test_resource_defs() {
    let test_resource_def = ResourceDef::default();
    let test_resource_instance = ResourceInstance::from(&test_resource_def);
    assert_eq!(test_resource_instance.id, 0);
    assert!(!test_resource_def.flags.is_roleplay);
    assert!(test_resource_def.flags.is_storable);
    println!("{:?}", test_resource_def);
}