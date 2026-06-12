use crate::sim::definitions::{Definitions};
use crate::sim::resource::{ResourceDef, ResourceFlags};
use crate::sim::settler::{Settler, SettlerMode};
use crate::sim::gamestate::GameState;

use crate::sim::building::BuildingDef;
use crate::sim::event::EventDef;
use crate::sim::tech::TechnologyDef;
use crate::dataio::meta::{TechMeta, SettlerMeta, ResourceMeta, BuildingMeta, MetaData};

use std::collections::HashMap;
use std::fs;
use std::fs::File;
use std::path::PathBuf;

use serde::Deserialize;


/// Loads the game state directly from a JSON file
pub fn load_game_state_from_json(base_path: impl AsRef<std::path::Path>) -> Result<GameState, String> {
    let path = base_path.as_ref().join("save.json");

    let data = std::fs::read_to_string(path)
        .map_err(|e| format!("Read error: {}", e))?;

    serde_json::from_str(&data)
        .map_err(|e| format!("Parse error: {}", e))
}

/// Pair parser. Takes in a string and returns an array of four tuple u32s
/// Invaluable for breaking things like 10:3,3:2,0:0,0:0 into usable information.
fn parse_resource_map(input: &str) -> HashMap<u32, f32> {
    let mut map = HashMap::new();

    for pair in input.split(',') {
        let mut parts = pair.split(':');

        let key = parts
            .next()
            .expect("missing resource id")
            .trim()
            .parse::<u32>()
            .expect("invalid resource id");

        let value = parts
            .next()
            .expect("missing amount")
            .trim()
            .parse::<f32>()
            .expect("invalid amount");

        // skip empty entries
        if key != 0 && value != 0.0 {
            map.insert(key, value);
        }
    }
    map
}

#[test]
fn test_resource_map_parser(){
    let my_vals = "3:3, 2:2, 1:1, 0:0".to_string();
    let test_mapping = parse_resource_map(&my_vals);
    println!("{:?}", test_mapping);
}



/// Settler/Citizen/Colonist struct and Shim.  The data is split between the meta(strings) and data (def)
#[derive(Deserialize)]
struct SettlerRecord{
    id:u32,
    name:String,
    age:u8,
    stamina:u8,
    health:u8,
    build_skill:u8,
    work_skill:u8,
    research_skill:u8,
    resource_affinity:u32,
    resource_affinity_name:String,
    resource_aversion:u32,
    resource_aversion_name:String,
}

fn load_settlers_from_csv(base_path: impl AsRef<std::path::Path>) -> (HashMap<u32,SettlerMeta>, HashMap<u32,Settler>){
    let mut settler_hash = HashMap::new();
    let mut settler_meta = HashMap::new();
    let path = base_path.as_ref().join("citizens.csv");
    let file = File::open(path).expect("Unable to open citizens.csv file.");
    let mut rdr = csv::Reader::from_reader(file);
    for result in rdr.deserialize(){
        let record:SettlerRecord = result.expect("Unable to read record in citizens.csv");
        let new_settler = SettlerMeta::new(
            record.name, 
            record.resource_affinity_name, 
            record.resource_aversion_name );
        settler_meta.insert(record.id, new_settler);
        let affinity = (record.resource_affinity > 0).then_some(record.resource_affinity);
        let aversion = (record.resource_aversion > 0).then_some(record.resource_aversion);
        let new_settler_def = Settler::new(
            record.id,
            record.health,
            record.age,
            record.stamina,
            record.build_skill,
            record.work_skill,
            record.research_skill,
            affinity,
            aversion,
            SettlerMode::Auto,
        );
        settler_hash.insert(record.id, new_settler_def);

    }

    (settler_meta, settler_hash)
}
#[test]
fn test_loading_settler_from_csv(){
    let base_path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("gamedata");
    let (test_meta, test_settler_defs) = load_settlers_from_csv(&base_path);
    assert!(test_meta.len() > 0);
    assert!(test_settler_defs.len() > 0);
        for item in test_meta.values(){
        println!("{}", item._describe());
    }
    for item in test_settler_defs.values(){
        println!("{:?}", item);
    }
}

#[derive(Deserialize)]
struct BuildingRecord{
    id:u32,
    //short_name:String,  //unused
    full_name:String,
    tech_required:u32,
    tech_required_name:String,
    resource_costs_names:String,
    resource_costs:String,
    input:String,
    input_names:String,
    output:String,
    output_names:String,
    storage:String,
    storage_names:String,
    construction_time:f32,
}

fn load_building_from_csv(base_path: impl AsRef<std::path::Path>) -> (HashMap<u32,BuildingMeta>,HashMap<u32,BuildingDef>){
    let mut building_hash = HashMap::new();
    let mut building_meta = HashMap::new();
    let path = base_path.as_ref().join("buildings.csv");
    let file = File::open(path).expect("Unable to open buildings.csv file.");
    let mut rdr = csv::Reader::from_reader(file);
    for result in rdr.deserialize(){
        let record: BuildingRecord = result.expect("Unable to read row in buildings.csv");
        let building_rec_meta = BuildingMeta::new(
            record.full_name,
            record.tech_required_name,
            record.resource_costs_names,
            record.input_names,
            record.output_names,
            record.storage_names,
            record.construction_time,
        );
        building_meta.insert(record.id, building_rec_meta);

        let tech_preqs = record.tech_required;
        let resource_costs = parse_resource_map(&record.resource_costs);
        let inputs = parse_resource_map(&record.input);
        let outputs = parse_resource_map(&record.output);
        let storage_capacity = parse_resource_map(&record.storage);
        let building_def = BuildingDef::new(
            record.id,
            tech_preqs,
            resource_costs,
            inputs,
            outputs,
            storage_capacity,
            record.construction_time,
        );
        building_hash.insert(record.id, building_def);
    }
    (building_meta, building_hash)
}

#[test]
fn test_building_load_and_meta(){
    let base_path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("gamedata");
    let (test_meta, test_building_defs) = load_building_from_csv(&base_path);
    assert!(test_meta.len() > 0);
    assert!(test_building_defs.len() > 0);
    for item in test_meta.values(){
        println!("{}", item._describe());
    }
    for item in test_building_defs.values(){
        println!("{:?}", item);
    }
}

/// Tech Record struct/shim.  Most of the data goes to the meta struct, the rest goes to the definition
#[derive(Deserialize)]
struct TechRecord {
    id: u32,
    //level: u32,
    name_level: String,
    name: String,
    prerequisites:String,
    named_prerequisites:String,
    //requirement:String,
    description:String,
    //notes:String,
    research_time:u32,
}


fn load_technology_from_csv(base_path: impl AsRef<std::path::Path>) -> (HashMap<u32, TechMeta>, HashMap<u32, TechnologyDef>) {
    let mut tech_hash = HashMap::new();
    let mut tech_meta = HashMap::new();
    let tech_path = base_path.as_ref().join("techs.csv");
    let file = File::open(tech_path).expect("Unable to open techs.csv file.");
    let mut rdr = csv::Reader::from_reader(file);

    for result in rdr.deserialize() {
        let record: TechRecord = result.expect("Unable to read row in techs.csv");
        // Set up metadata first
        let rec_metadata = TechMeta::new(record.name_level, record.name, record.named_prerequisites,
        record.description, record.research_time);
        tech_meta.insert(record.id, rec_metadata);

        let mut iter = record.prerequisites
        .split(',')
        .map(|s| s.trim().parse::<u32>());
        let preqs = [
            iter.next().transpose().expect("parse error").expect("missing value"),
            iter.next().transpose().expect("parse error").expect("missing value"),
            iter.next().transpose().expect("parse error").expect("missing value"),
            iter.next().transpose().expect("parse error").expect("missing value"),
        ];
        
        if iter.next().is_some() {
            panic!("Too many values in prerequisites in techs.csv");
        }
        let tech_def = TechnologyDef::new(record.id, preqs, record.research_time as f32);
        tech_hash.insert(record.id, tech_def);
    }

    (tech_meta, tech_hash)
}

#[test]
fn test_tech_load_and_meta() {
    let base_path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("gamedata");
    let (test_meta, test_tech_defs) = load_technology_from_csv(&base_path);
    let number_tech_meta = test_meta.len();
    assert_ne!(number_tech_meta, 0);
    assert!(test_tech_defs.len() > 0);
    assert_eq!(test_meta.len(), test_tech_defs.len());
    println!("Tech values imported");
    for item in test_meta.values(){
        println!("{}", item._describe());
    }
    println!("Tech values and imports listed");
    for item in test_tech_defs.values(){
        println!("{}", item._describe());
    }
}

/// Resource record
#[derive(Deserialize)]
struct ResourcesRecord {
    id: u32,
    name:String,
    description:String,
    is_roleplay:bool,
    is_storable:bool,
}

fn load_resources_from_csv(base_path: impl AsRef<std::path::Path>) -> (HashMap<u32, ResourceMeta>, HashMap<u32, ResourceDef>){
    let mut resource_hash: HashMap<u32, ResourceDef> = HashMap::new();
    let mut resource_meta: HashMap<u32, ResourceMeta> = HashMap::new();
    let path = base_path.as_ref().join("resources.csv");
    let file = File::open(path).expect("Unable to open resources.csv file.");
    let mut rdr = csv::Reader::from_reader(file);
    for result in rdr.deserialize(){
        let record:ResourcesRecord = result.expect("Unable to read row in resources.csv");
        //  Flags and Def will have to be imported separately
        
        let resource_flags = ResourceFlags::new(record.is_roleplay, record.is_storable);
        let resource_def = ResourceDef::new(record.id, resource_flags);
        let resource_meta_item = ResourceMeta::new(record.name, record.description);
        resource_hash.insert(record.id, resource_def);
        resource_meta.insert(record.id, resource_meta_item);
    }

    (resource_meta, resource_hash)
}

#[test]
fn test_resource_load_and_meta(){
    let base_path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("gamedata");
    let (test_meta, test_resource_defs) = load_resources_from_csv(&base_path);
    assert!(test_meta.len() > 0);
    assert!(test_resource_defs.len() > 0);
    assert_eq!(test_meta.len(), test_resource_defs.len());
    println!("Resources imported");
    for item in test_meta.values(){
        println!("{}", item._describe());
    }
    println!("Resource meta imports listed");
    for item in test_resource_defs.values(){
        println!("{}", item._describe());
    }
}

fn load_events(base_path: impl AsRef<std::path::Path>) -> HashMap<u32, EventDef> {
    let path = base_path.as_ref().join("events.json");

    let data = fs::read_to_string(path)
        .expect("Unable to read events.json file.");

    let events: Vec<EventDef> = serde_json::from_str(&data)
        .expect("Unable to parse events.json");

    events.into_iter().map(|e|  (e.id, e)).collect()
}


#[test]
fn test_load_events(){
        let base_path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("gamedata");
        let test_events = load_events(&base_path);
        assert!(test_events.len() > 0);
        for (_id, event) in test_events{
            println!("{:?}", event);
        }
}

pub fn load_definitions_and_meta() -> (Definitions, MetaData){
    // Our ready to use hashmaps, ready to be consumed by the Definitions new() function
    let base_path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("gamedata");
    let (settler_meta, settler_defs) = load_settlers_from_csv(&base_path);
    let (building_meta, building_defs) = load_building_from_csv(&base_path);
    let (tech_meta, technology_defs) = load_technology_from_csv(&base_path);
    let (resource_meta, resource_defs) = load_resources_from_csv(&base_path);
    let event_defs:HashMap<u32,EventDef> = load_events(&base_path);
    let game_definition:Definitions = Definitions::new(
        settler_defs,
        building_defs,
        technology_defs,
        resource_defs,
        event_defs,
    );
    let game_meta_data:MetaData = MetaData::new(
        tech_meta,
        settler_meta,
        building_meta,
        resource_meta,
    );
    (game_definition, game_meta_data)
}

#[test]
fn test_load_defs (){
    use std::mem;
    let (test_defs, test_meta) = load_definitions_and_meta();
    assert!(mem::size_of_val(&test_defs) > 0);
    assert!(mem::size_of_val(&test_meta) > 0);
}
