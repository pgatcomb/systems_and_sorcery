/*
Metadata Structs
These are required to show the user 'pretty strings' other UI data
*/
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
#[derive(Serialize, Deserialize, Clone, Default)]
pub struct MetaData {
    tech_meta:HashMap<u32, TechMeta>,
    settler_meta:HashMap<u32, SettlerMeta>,
    building_meta:HashMap<u32, BuildingMeta>,
    resource_meta:HashMap<u32, ResourceMeta>,
}


impl MetaData{
    pub fn new(tech_meta:HashMap<u32, TechMeta>, settler_meta:HashMap<u32, SettlerMeta>, 
    building_meta:HashMap<u32, BuildingMeta>, resource_meta:HashMap<u32, ResourceMeta>) -> MetaData{
        MetaData{    
            tech_meta,
            settler_meta,
            building_meta,
            resource_meta,
            }
    }
}
#[derive(Serialize, Deserialize, Clone)]
pub struct SettlerMeta{
    name: String,
    resource_affinity: String,
    resource_aversion: String,
}

impl SettlerMeta{
    pub fn new(name:String, resource_affinity:String, resource_aversion:String) -> SettlerMeta{
        SettlerMeta { name, resource_affinity, resource_aversion }
    }
    pub fn _describe(&self) -> String{
        format!("{} {} {}", self.name, self.resource_affinity, self.resource_aversion)
    }
}
#[derive(Serialize, Deserialize, Clone)]
pub struct TechMeta{
    name_level:String,
    name:String,
    named_prerequisites:String,
    description:String,
    research_time:u32,
}

impl TechMeta{
    pub fn new(name_level:String, name: String, named_prerequisites:String, description: String, research_time:u32) -> TechMeta{
        TechMeta { name_level, name, named_prerequisites, description, research_time }
    }
    pub fn _describe(&self) -> String{
        format!("{} {} {} {} {} Research Time: {} turns", self.name, self.name_level, self.named_prerequisites, self.description, self.name_level, self.research_time)
    }
}
#[derive(Serialize, Deserialize, Clone)]
pub struct ResourceMeta{
    name: String,
    description:String,
}

impl ResourceMeta{
    pub fn new(name:String, description: String) -> ResourceMeta{
        ResourceMeta{name, description}
    }

    pub fn _describe(&self) -> String{
        format!("Resource name: {} Desc: {}", self.name, self.description)
    }

}
#[derive(Serialize, Deserialize, Clone)]
pub struct BuildingMeta{
    name: String,
    tech_required_name:String,
    resource_costs_names:String,
    input_names:String,
    output_names:String,
    storage_names:String,
    construction_time:f32,
}
impl BuildingMeta{
    pub fn new(name: String,tech_required_name:String,resource_costs_names:String,input_names:String,output_names:String,storage_names:String,construction_time:f32) -> BuildingMeta{
        BuildingMeta { name, tech_required_name, resource_costs_names, input_names, output_names, storage_names, construction_time }
    }
    pub fn _describe(&self) -> String{
        format!("{} {} {} {} {} {} {}",self.name, self.tech_required_name, self.resource_costs_names, self.input_names, self.output_names, self.storage_names, self.construction_time)
    }
}