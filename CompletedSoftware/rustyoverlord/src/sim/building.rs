use std::collections::HashMap;
use serde::{Serialize, Deserialize};
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct BuildingDef {
    pub id: u32,
    required_tech: u32,
    resource_costs: HashMap<u32, f32>,
    pub inputs: HashMap<u32, f32>,
    pub outputs: HashMap<u32, f32>,
    pub storage_capacity: HashMap<u32, f32>,
    pub build_time: f32,
    //footprint: u16,
}

impl Default for BuildingDef{
    /// Initializes a building with costs of 10 of resource 1. It has an input of 5.0 of resource 1 and it outputs and stores
    /// 10.0 of resource 2 and 10.0 of resource 3
    fn default() -> BuildingDef{
        let resource_costs: HashMap<u32, f32> = HashMap::from([(1, 10.0), (0, 0.0)]);
        let inputs: HashMap<u32, f32> = HashMap::from([(1,5.0), (0,0.0)]);
        let outputs: HashMap<u32, f32> = HashMap::from([(2,10.0),(3,10.0)]);
        let storage_capacity: HashMap<u32, f32> = HashMap::from([(2,10.0),(3,10.0)]);
        BuildingDef {
            id:0,
            required_tech:0,
            resource_costs,
            inputs,
            outputs,
            storage_capacity,
            build_time: 1.0,
            //footprint: 0, //Not implemented
        }
    }
}

impl BuildingDef{

    pub fn new(id:u32, required_tech:u32, resource_costs: HashMap<u32, f32>,inputs:HashMap<u32, f32>, outputs:HashMap<u32, f32>, storage_capacity:HashMap<u32, f32>,
    build_time: f32) -> BuildingDef{
        BuildingDef {id, required_tech,resource_costs, inputs,outputs,storage_capacity,build_time}
    }

}

/// The building instance represents an actual building and its progress. Progress 1.0 is required for functionality
#[derive(Serialize, Deserialize, Clone)]
pub struct BuildingInstance {
    pub id: u32, // refers to BuildingDef
    pub progress: f32,
}

impl Default for BuildingInstance {
    fn default() -> Self {
        BuildingInstance {
            id: 0,
            progress: 0.0,
        }
    }
}

impl BuildingInstance{
    /// Unused, use from instead
    pub fn _new(id: u32, progress: f32) -> BuildingInstance {
        BuildingInstance { id, progress }
    }
}

impl From<&BuildingDef> for BuildingInstance {
    fn from(building_def:&BuildingDef) -> Self{
        BuildingInstance {id: building_def.id, progress:0.0}
    }
}

#[test]
fn test_new_building_def(){
    let test_building = BuildingDef::default();
    assert_eq!(test_building.id, 0);
    assert_eq!(test_building.inputs.get(&0), Some(&0.0));
    assert_eq!(test_building.inputs.get(&1), Some(&5.0));
    assert_eq!(test_building.outputs.get(&2), Some(&10.0));
    assert_eq!(test_building.outputs.get(&3), Some(&10.0));
    assert_eq!(test_building.storage_capacity.get(&0), None);
    assert_eq!(test_building.storage_capacity.get(&2), Some(&10.0));
    assert_eq!(test_building.storage_capacity.get(&3), Some(&10.0));
    println!("{:?}", test_building);
}

#[test]
fn test_new_building_inst(){
    let test_building_instance = BuildingInstance::default();
    assert_eq!(test_building_instance.id, 0);
    assert_eq!(test_building_instance.progress, 0.0);
}

#[test]
fn test_building_from_ref(){
    let test_building = BuildingDef::default();
    let test_building_instance: BuildingInstance = BuildingInstance::from(&test_building);
    assert_eq!(test_building_instance.id, 0);
    assert_eq!(test_building_instance.progress, 0.0);
}