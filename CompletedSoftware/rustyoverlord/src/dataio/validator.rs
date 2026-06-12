/*
The validator exists to go through all the imported data and validate if it is created correctly.
It will identify any issues such as missing resources, values, looping references, impossible to reach events, etc.

*/
use crate::sim::definitions::{Definitions};
use std::time::{Instant, Duration};

/// Validator takes the loaded definitions and tests them meticulously
pub fn validate_definitions(defs: &Definitions) -> Result<(), Vec<String>>{
    println!("Validating data...");
    let time_now = Instant::now();
    let mut errors: Vec<String> = Vec::new();
    println!("Validating buildings...");
    defs.validate_buildings(&mut errors);
    println!("Validating settlers...");
    defs.validate_settlers(&mut errors);
    println!("Validating techs...");
    defs.validate_techs(&mut errors);
    print!("Validating events...");
    defs.validate_events(&mut errors);
    let dur: Duration = time_now.elapsed();
    if errors.is_empty() {
        println!("...complete in {:?}", dur);
        Ok(())
    } else {
        Err(errors)
    }

}