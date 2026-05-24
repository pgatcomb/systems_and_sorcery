use serde::{Serialize, Deserialize};
static AMBIENT_TEMP: f32 = 293.0; // Kelvin
static DIAGONAL_EFFECT: f32 = std::f32::consts::FRAC_1_SQRT_2;   // Diagonal effect of a neighbor
static FLUX_TO_WATT: f32 = 1000.0;      // How many watts we get per unit of flux
static COOLANT_BOILING_POINT: f32 = 395.0;   //393 = boiling for water
static DELTA_T: f32 = 0.1;
static FUEL_ROD_MASS: f32 = 15.0; 
static MASS_OF_COOLANT: u32 = 6000;
static SEC_COOLING_SCALE:f32 = 5.0;
static PRIM_HEAT_SCALE:f32 = 10.0;


#[derive(Debug, PartialEq)]
pub struct ReactorComponent{
    pub id:usize,
    pub temperature:f32,    // Kelvin
    pub condition:f32,      // 0.0 - 1.0
    pub neighbors:[Option<usize>; 8], // N -> NE -> E -> SE -> S -> SW -> W -> NW
    pub component_type:ReactorComponentType,
    pub absorption:f32, // How much this reduces the reaction
    pub moderation:f32, // How much this increases the reaction.  Acts as a multipler to flux.
    pub position:f32,   // Modifies the overall 'effect' of its moderation and flux.  We can use this to extract a control rod or pull a fuel rod right out
    pub flux:f32,       // The base amount of flux produced
    pub reactivity:f32, // How sensitive the conversion of flux into heat is. E.g. LEU = low reactivity, HEU = very high reactivity. High reactivity = more flux.
}

#[derive(PartialEq, Debug)]
pub enum ReactorComponentType{
    ControlRod,
    FuelRod,
    Wall,
    Moderator,
}

/// Reactor telemetry struct for data out
#[derive(Serialize, Debug, Clone)]
pub struct ReactorTelemetry{
    pub tick: usize,
    pub primary_coolant_loop_temperature: f32,
    pub secondary_coolant_loop_temperature: f32,
    pub primary_coolant_loop_speed: f32,
    pub secondary_coolant_loop_speed: f32,
    pub component_temperatures: Vec<f32>,
    pub component_positions: Vec<f32>,
}

impl Default for ReactorTelemetry {
    fn default() -> Self {
        ReactorTelemetry {
            tick: 0,
            primary_coolant_loop_temperature: AMBIENT_TEMP,
            secondary_coolant_loop_temperature: AMBIENT_TEMP,
            primary_coolant_loop_speed: 0.0,
            secondary_coolant_loop_speed: 0.0,
            component_temperatures: Vec::new(),
            component_positions: Vec::new(),
        }
    }
}


#[derive(Debug, Serialize, Deserialize)]
/// Reactor command enum. Scram = All rods in, Pumps to maximum RPM
/// Control Rod position takes a specific rod _or_ all rods as input
/// Pump speed can be primary or secondary plus speed
pub enum ReactorCommand{
    None,
    Scram,
    SetControlRodPosition{id: Option<usize>, position: f32},
    SetPumpSpeed{loop_type: CoolantLoopType, speed: f32},
    Shutdown,
}

#[derive(Debug)]
pub struct CoolantLoop{
    pub id: usize,
    pub pump_type: CoolantLoopType,
    pub temperature: f32,
    pub pump_speed: f32,
    pub conductivity: f32,
}

#[derive(PartialEq, Debug, Serialize, Deserialize)]
pub enum CoolantLoopType{
    Primary,
    Secondary,
}

#[derive(Debug)]
pub struct Reactor{
    pub name: String,
    pub components: Vec<ReactorComponent>,
    pub width: usize,
    pub height: usize,
    pub loops: Vec<CoolantLoop>, // Changed to pub for external access
    pub coolant_mass: u32,
    pub tick: usize,
}

/// A component of the reactor, one of the grid cells.
impl ReactorComponent{
    /// Base default of all reactor components
    pub fn base(id:usize) -> Self{
        Self {
            id,
            temperature: AMBIENT_TEMP,
            condition: 1.0,
            neighbors: [None; 8],
            component_type: ReactorComponentType::Wall,
            absorption: 0.0,
            moderation: 0.0,
            position: 1.0,
            flux: 0.0,
            reactivity: 0.0,      
        }
    }

    /// This function allows you to SET the position of the component, clamped between 0.0 and 1.0
    pub fn set_position(&mut self, new_position: f32){
        self.position = new_position.clamp(0.0, 1.0);
    }

    /// This function ADJUSTS the position of the component, clamped between 0.0 and 1.0
    pub fn adjust_position(&mut self, delta_position: f32){
        self.position = (self.position + delta_position).clamp(0.0, 1.0);
    }

    /// This function allows you to SET the temperature of the component, clamped to a minumum of 0.0 Kelvin
    pub fn set_temperature(&mut self, new_temperature: f32){
        self.temperature = new_temperature.max(0.0);
    }

    /// This function changes the current temperature by a temperature delta, clamped to a minumum of 0.0 Kelvin
    pub fn adjust_temperature(&mut self, delta_temperature: f32){
        self.temperature = (self.temperature + delta_temperature).max(0.0);
    }

    /// This function allows you to SET the component's condition clamped between 0 and 1
    pub fn set_condition(&mut self, new_condition: f32){
        self.condition = new_condition.clamp(0.0, 1.0);
    }

    /// This function CHANGES the component's condition, clamped between 0 and 1
    pub fn adjust_condition(&mut self, delta_condition: f32){
        self.condition = (self.condition + delta_condition).clamp(0.0, 1.0);
    }

    /// This function creates a new wall which has no special properties
    pub fn new_wall(id: usize) -> Self {
        Self::base(id)
    }

    pub fn is_fuel(&self) -> bool{
        self.component_type == ReactorComponentType::FuelRod
    }
    /// This function creates a new control rod in full DOWN position
    pub fn new_control_rod(id: usize) -> Self {
        let mut c: ReactorComponent = Self::base(id);
        c.component_type = ReactorComponentType::ControlRod;
        c.absorption = 1.0;
        c
    }

    /// This function creates a new moderator rod that has the unique quality of creating a negative moderation to enhance a reaction
    pub fn new_moderator(id:usize) -> Self{
        let mut c: ReactorComponent = Self::base(id);
        c.component_type = ReactorComponentType::Moderator;
        c.moderation = 1.0;
        c
    }
    /// This function creates a new LEU fuel rod with modest reactivity
    pub fn new_leu_rod(id:usize) -> Self{
        let mut c: ReactorComponent = Self::base(id);
        c.component_type = ReactorComponentType::FuelRod;
        c.reactivity = 0.5;
        c.flux = 1.0;
        c
    }
    /// This function creates a new fuel rod with high reactivity
    pub fn new_heu_rod(id:usize) -> Self{
        let mut c: ReactorComponent = Self::base(id);
        c.component_type = ReactorComponentType::FuelRod;
        c.reactivity = 1.0;
        c.flux = 1.0;
        c

    }
}

impl CoolantLoop{
    /// Base default of all coolant loops
    pub fn new(id: usize, pump_type: CoolantLoopType, temperature: f32, pump_speed: f32, conductivity: f32) -> Self{
        Self{
            id,
            pump_type,
            temperature,
            pump_speed,
            conductivity,
        }
    }

    /// Create a basic primary coolant loop
    pub fn default_primary_coolant_loop(id: usize) -> Self{
        Self::new(id, CoolantLoopType::Primary, AMBIENT_TEMP, 0.25, 75.0)
    }

    /// Create a  basic secondary coolant loop
    pub fn default_secondary_coolant_loop(id: usize) -> Self{
        Self::new(id, CoolantLoopType::Secondary, AMBIENT_TEMP, 0.25, 25.0)
    }

    /// SET the of the coolant in the coolant loop
    pub fn set_temperature(&mut self, temp: f32) {
        self.temperature = temp.max(0.0);
    }

    /// ADJUST the temperature in the coolant loop
    pub fn adjust_temperature(&mut self, delta: f32) {
        self.set_temperature(self.temperature + delta);
    }

    /// SET the speed of the pump limited to min to max (0.0 to 1.0)
    pub fn set_pump_speed(&mut self, speed: f32) {
        self.pump_speed = speed.clamp(0.0, 1.0);
    }

    /// ADJUST the speed of the pump limited to min to max (0.0 to 1.0)
    pub fn adjust_pump_speed(&mut self, delta: f32) {
        self.set_pump_speed(self.pump_speed + delta);
    }

}

impl Reactor{
    /// Initalizes a default reactor with a size of width x height with 'wall' around the outside
    pub fn new(name: String, width: usize, height: usize) -> Reactor{
        let primary_coolant_loop: CoolantLoop = CoolantLoop::default_primary_coolant_loop(0);
        let secondary_coolant_loop: CoolantLoop = CoolantLoop::default_secondary_coolant_loop(1);
        let default_components: Vec<ReactorComponent> = Self::get_default_components(width, height);
        let components = Self::calculate_neighbors(default_components, width, height);

        let loops: Vec<CoolantLoop> = vec![primary_coolant_loop, secondary_coolant_loop];
        Reactor{
            name,
            components,
            width,
            height,
            loops,
            coolant_mass:MASS_OF_COOLANT,
            tick:0,
        }
    }

    /// This function takes in a Vector of components and calculates their neighbors based on the size of the reactor in an xy grid
    ///       7    0    1
    ///       6  object 2 
    ///       5    4    3
    /// 
    fn calculate_neighbors(components: Vec<ReactorComponent>, width: usize, height:usize) -> Vec<ReactorComponent>{
        let mut components_with_neighbors: Vec<ReactorComponent> = Vec::new();
        for component in components{
            let mut neighbors: [Option<usize>; 8] = [None; 8];
            let id = component.id;
            let x = (id % width) as i32;
            let y = (id / width) as i32;
            let offsets = [
                (0, -1),  // 0: N
                (1, -1),  // 1: NE
                (1, 0),   // 2: E
                (1, 1),   // 3: SE
                (0, 1),   // 4: S
                (-1, 1),  // 5: SW
                (-1, 0),  // 6: W
                (-1, -1), // 7: NW
            ];

            for (i, (dx, dy)) in offsets.iter().enumerate() {
                let nx = x + dx;
                let ny = y + dy;

                if nx >= 0 && nx < width as i32 && ny >= 0 && ny < height as i32 {
                    neighbors[i] = Some((ny as usize) * width + (nx as usize));
                }
            }

            components_with_neighbors.push(ReactorComponent {
                neighbors,
                ..component
            })
        }
        components_with_neighbors
    }

    /// This function gets a vector of components with of a 'waffle pattern' reactor with a wall along the outside
    fn get_default_components(width: usize, height: usize) -> Vec<ReactorComponent>{
        let mut components: Vec<ReactorComponent> = Vec::new();
        for y in 0..height{
            for x in 0..width{
                let id = y * width + x;
                // If we are on the outside of the reactor, our component should be a wall
                if x == 0 || y == 0 || x == width - 1 || y == height - 1{
                    components.push(ReactorComponent::new_wall(id));
                    continue;  // continue inner loop, no need to check next two values                
                }
                if x % 2 == 0{
                    components.push(ReactorComponent::new_control_rod(id));
                }
                else{
                    components.push(ReactorComponent::new_leu_rod(id));
                }
            }

        }
        components
    }

    /// Function returns the current tick the reactor is on
    pub fn get_tick(&self) -> usize{
        self.tick
    }

    /// Function to return the average temperature of the coolant in a general circuit
    pub fn get_circuit_ave_temperatures(&self, typ:CoolantLoopType) -> f32{
        let mut number_cool_pumps:f32 = 0.0;
        let mut coolant_ave_temp:f32 = 0.0;
        for circuit in &self.loops{
            if typ == circuit.pump_type{
                coolant_ave_temp += circuit.temperature;
                number_cool_pumps += 1.0;
            }
        }
        if number_cool_pumps == 0.0{
            return AMBIENT_TEMP;
        }
        coolant_ave_temp / number_cool_pumps
    }

    /// Function goes through each component and calculates the new temperature based on its neighbors
    /// This is a two pass operation. The first pass will sum up all the values and calculate the deltas
    /// The second pass will apply the deltas to the components
    /// Function returns the total flux
    fn update_reactor_components(&mut self) -> Result<f32, String>{
        let mut deltas = vec![0.0; self.components.len()];
        let mut total_flux: f32 = 0.0;
        for (id, _component) in self.components.iter().enumerate() {
        //for id in 0..self.components.len() {
            let mut neighbor_flux_sum: f32 = 0.0;
            let mut neighbor_moderation_sum: f32 = 0.0; 
            let mut neighbor_absorption_sum: f32 = 0.0;
            let mut total_neighbors: f32 = 0.0;

            for inx in 0..8{
                if self.components[id].neighbors[inx].is_none(){
                    continue;
                }
                total_neighbors += 1.0;
                let neighbor_id: usize = self.components[id].neighbors[inx].unwrap();
                let diagonal_modifier: f32 = match inx % 2{
                    0 => 1.0,
                    _ => DIAGONAL_EFFECT,
               };
                neighbor_flux_sum += self.components[neighbor_id].flux * diagonal_modifier;
                neighbor_moderation_sum += self.components[neighbor_id].moderation * diagonal_modifier;
                neighbor_absorption_sum += self.components[neighbor_id].absorption * diagonal_modifier * self.components[neighbor_id].position;
                }
            let ave_flux: f32 = neighbor_flux_sum / total_neighbors.max(1.0);     
            let ave_moderation = neighbor_moderation_sum / total_neighbors.max(1.0);
            let ave_absorption = neighbor_absorption_sum / total_neighbors.max(1.0);
            
            let moderation = ave_moderation.clamp(0.0, 1.0);
            let absorption = ave_absorption.clamp(0.0, 1.0);
            
            // Logic fix: Moderation increases reaction, Absorption decreases it.
            let effective_flux: f32 = (self.components[id].flux + ave_flux) *
                                        self.components[id].reactivity * 
                                        (1.0 + moderation) * 
                                        (1.0 - absorption);
            total_flux += effective_flux;
            let delta:f32 = (effective_flux * FLUX_TO_WATT * DELTA_T / FUEL_ROD_MASS).clamp(-5.0, 5.0);
            deltas[id] = delta;     
        }
        for (component, delta) in self.components.iter_mut().zip(deltas) {
            component.adjust_temperature(delta);
        }

        Ok(total_flux)
    }

    fn get_average_fuel_temperature(&self) -> f32{
        let mut total_rods: f32 = 0.0;
        let mut total_temperature: f32 = 0.0;
        for component in &self.components{
            if let ReactorComponentType::FuelRod = component.component_type{
                total_rods += 1.0;
                total_temperature += component.temperature;
            }
        }
        (total_temperature / total_rods).max(AMBIENT_TEMP)
    }


    fn update_coolant_temperatures(&mut self) -> Result <f32, String>{
        let average_fuel_temp = self.get_average_fuel_temperature();
        let mut total_heat_extracted_from_fuel:f32 = 0.0;
        let mut total_heat_passed_to_secondary:f32 = 0.0;
        let secondary_coolant_ave_temp = self.get_circuit_ave_temperatures(CoolantLoopType::Secondary);
        for circuit in &mut self.loops{
            if circuit.pump_type == CoolantLoopType::Primary{
            let core_heating: f32 = circuit.pump_speed * circuit.conductivity *
                               (average_fuel_temp - circuit.temperature);
            let exchanger_cooling:f32 = circuit.pump_speed * circuit.conductivity *
                                (circuit.temperature - secondary_coolant_ave_temp) * PRIM_HEAT_SCALE;
            let net_primary_energy:f32 = core_heating - exchanger_cooling;
            let delta_t = net_primary_energy / (self.coolant_mass) as f32;
            circuit.temperature += delta_t.clamp(-25.0, 25.0) * DELTA_T;
            total_heat_extracted_from_fuel += core_heating;
            total_heat_passed_to_secondary += exchanger_cooling;
            }
        }
        let secondary_pump_count = self.loops.iter()
                .filter(|c| c.pump_type == CoolantLoopType::Secondary).count() as f32;            
        let heat_per_secondary_loop = total_heat_passed_to_secondary / secondary_pump_count.max(1.0);

        for circuit in &mut self.loops {
            if circuit.pump_type == CoolantLoopType::Secondary {             
                let steam_modifier:f32 = if circuit.temperature >= COOLANT_BOILING_POINT {2.0} else {1.0};
                let environmental_cooling = circuit.pump_speed * circuit.conductivity *
                                            (circuit.temperature - AMBIENT_TEMP) * steam_modifier * SEC_COOLING_SCALE;
                let net_secondary_energy = heat_per_secondary_loop - environmental_cooling;
                let delta_t = net_secondary_energy / (self.coolant_mass) as f32;
                circuit.temperature += delta_t.clamp(-25.0, 25.0) * DELTA_T;
                //println!("{}-{}-{}",environmental_cooling,net_secondary_energy,delta_t);
            }
        }
        Ok(total_heat_extracted_from_fuel)
    }

    fn update_fuel_cell_temps(&mut self, heat_removed:f32){
        let fuel_rod_count = self.components.iter().filter(|c| c.is_fuel()).count() as f32;
        if fuel_rod_count == 0.0 { return; }

        let temp_drop_per_rod = (heat_removed * DELTA_T / fuel_rod_count) / FUEL_ROD_MASS;

        for cell in &mut self.components {
            if cell.is_fuel() {
                cell.temperature = (cell.temperature - temp_drop_per_rod).max(AMBIENT_TEMP);
            }
        }   
    }
    
    /// Function writes telemetry to the struct
    pub fn get_telemetry(&self) -> ReactorTelemetry{
        let primary = self.loops.iter().find(|l| l.pump_type == CoolantLoopType::Primary);
        let secondary = self.loops.iter().find(|l| l.pump_type == CoolantLoopType::Secondary);

        ReactorTelemetry{
            tick: self.tick,
            primary_coolant_loop_temperature: primary.map(|l| l.temperature).unwrap_or(AMBIENT_TEMP),
            secondary_coolant_loop_temperature: secondary.map(|l| l.temperature).unwrap_or(AMBIENT_TEMP),
            primary_coolant_loop_speed: primary.map(|l| l.pump_speed).unwrap_or(0.0),
            secondary_coolant_loop_speed: secondary.map(|l| l.pump_speed).unwrap_or(0.0),
            component_temperatures: self.components.iter().map(|c| c.temperature).collect(),
            component_positions: self.components.iter().map(|c| c.position).collect(),
        }
    }

    /// This function takes the ReactorCommand Enum and issues the appropriate commands.
    pub fn handle_commands(&mut self, command: ReactorCommand) -> Result<(), String> {
        match command {
            ReactorCommand::None => {},
            ReactorCommand::Shutdown => {},
            ReactorCommand::Scram => {
                // Safety: Immediately move all control rods to full insertion and maximize coolant flow
                for component in &mut self.components {
                    if component.component_type == ReactorComponentType::ControlRod {
                        component.set_position(1.0);
                    }
                }
                for circuit in &mut self.loops {
                    circuit.set_pump_speed(1.0);
                }
            }
            ReactorCommand::SetControlRodPosition { id, position } => {
                match id {
                    Some(target_id) => {
                        // Safely retrieve the component and verify it is a control rod
                        let component = self.components.get_mut(target_id)
                            .ok_or_else(|| format!("Component ID {} not found", target_id))?;
                        
                        if component.component_type != ReactorComponentType::ControlRod {
                            return Err(format!("Component ID {} is not a control rod", target_id));
                        }
                        component.set_position(position);
                    }
                    None => {
                        // Apply to all control rods
                        for component in &mut self.components {
                            if component.component_type == ReactorComponentType::ControlRod {
                                component.set_position(position);
                            }
                        }
                    }
                }
            }
            ReactorCommand::SetPumpSpeed { loop_type, speed } => {
                for circuit in &mut self.loops {
                    if circuit.pump_type == loop_type {
                        circuit.set_pump_speed(speed);
                    }
                }
            }
        }
        Ok(())
    }

    /// Function processes all changes to the reactor and upates states
    pub fn tick(&mut self) -> Result<(), String>{
        // Step 1: Update the temperature of all ReactorComponents
        match self.update_reactor_components() {
            Ok(_) => {},
            Err(e) => return Err(e),
        };
        // Step 2: Update the coolant Temperatures

        let heat_removed = self.update_coolant_temperatures()?;
        
        // Step 3: Remove any heat taken from the control rods
        self.update_fuel_cell_temps(heat_removed);

        // Step 4: Write telemetry
        //let telemetry = self.get_telemetry();

        // Step 5: Increment Tick
        self.tick += 1;
        Ok(())
    }

}

/// Test creation of a reactor
#[test]
fn test_reactor(){
    let mut my_reactor = Reactor::new("Nuclear Reactor".to_string(), 7,7);
    // Print the grid of components carefully
    let mut id = 0;
    for y in 0..my_reactor.height{
        for x in 0..my_reactor.width{
            println!("{x}/{y} - {:?}:{:?} {:?}", id, my_reactor.components[id].component_type, my_reactor.components[id].neighbors);
            id += 1;
        }
    }
    println!();
    for _x in 0..100{
        my_reactor.tick().expect("Something failed in the reactor tick");
        println!("{}K\t{}K", my_reactor.loops[0].temperature, my_reactor.loops[1].temperature);
    }
    for x in 0..my_reactor.width * my_reactor.height{
        //println!("{:?}", my_reactor.components[x]);
    }
    println!("Primary Coolant Loop Temp:{}, Secondary Coolant Loop Temp: {}", my_reactor.get_circuit_ave_temperatures(CoolantLoopType::Primary), my_reactor.get_circuit_ave_temperatures(CoolantLoopType::Secondary));
}

/// Test creation and invariants of our control rods
#[test]
fn test_reactor_components(){
    let my_wall: ReactorComponent = ReactorComponent::new_wall(0);
    assert_eq!(my_wall.component_type, ReactorComponentType::Wall);
    assert_eq!(my_wall.absorption, 0.0);
    
    let mut my_control_rod: ReactorComponent = ReactorComponent::new_control_rod(1);
    assert_eq!(my_control_rod.component_type, ReactorComponentType::ControlRod);
    assert_eq!(my_control_rod.absorption, 1.0);

    let my_moderator: ReactorComponent = ReactorComponent::new_moderator(2);
    assert_eq!(my_moderator.component_type, ReactorComponentType::Moderator);
    assert_eq!(my_moderator.moderation, 1.0);

    let my_leu_rod: ReactorComponent = ReactorComponent::new_leu_rod(3);
    assert_eq!(my_leu_rod.component_type, ReactorComponentType::FuelRod);
    assert_eq!(my_leu_rod.reactivity, 0.5);

    let my_heu_rod: ReactorComponent = ReactorComponent::new_heu_rod(4);
    assert_eq!(my_heu_rod.component_type, ReactorComponentType::FuelRod);
    assert_eq!(my_heu_rod.reactivity, 1.0);

    // Jam the control rod to the full inserted position.
    my_control_rod.adjust_position(50.0);
    assert_eq!(my_control_rod.position, 1.0);

    // Jam the control rod to the full out position
    my_control_rod.set_position(-1.0);
    assert_eq!(my_control_rod.position, 0.0);

    // Let's heat up the control rod
    my_control_rod.adjust_temperature(500.0);
    assert_eq!(my_control_rod.temperature, 500.0+AMBIENT_TEMP);

    // Let's defy physics and chill our rod a bit
    my_control_rod.set_temperature(-500.0);
    assert_eq!(my_control_rod.temperature, 0.0);

    // Destroy our control rod
    my_control_rod.adjust_condition(-9.0);
    assert_eq!(my_control_rod.condition, 0.0);

    // Set our control rod to perfect condition
    my_control_rod.set_condition(10.0);
    assert_eq!(my_control_rod.condition, 1.0);

    println!("{:?}", my_control_rod);

}

#[test]
fn test_coolant_circuits(){
    // Primary coolant creation test
    let mut my_primary_circuit:CoolantLoop = CoolantLoop::default_primary_coolant_loop(0);
    assert_eq!(my_primary_circuit.pump_type, CoolantLoopType::Primary);
    assert_eq!(my_primary_circuit.conductivity,75.0);

    // Secondary coolant creation test
    let my_secondary_circuit:CoolantLoop = CoolantLoop::default_secondary_coolant_loop(1);
    assert_eq!(my_secondary_circuit.pump_type, CoolantLoopType::Secondary);
    assert_eq!(my_secondary_circuit.conductivity, 25.0);

    // Crank up the pump speed and check that it caps out at 1.0 (full speed)
    my_primary_circuit.adjust_pump_speed(11.0);
    assert_eq!(my_primary_circuit.pump_speed, 1.0);

    // Try to set the pump speed to negative
    my_primary_circuit.set_pump_speed(-1.0);
    assert_eq!(my_primary_circuit.pump_speed, 0.0);

    // Heat up the coolant
    my_primary_circuit.adjust_temperature(100.0);
    assert_eq!(my_primary_circuit.temperature, 100.0+AMBIENT_TEMP);

    // Cool down the coolant excessively
    my_primary_circuit.set_temperature(-42.0);
    assert_eq!(my_primary_circuit.temperature, 0.0);

    println!("{:?}", my_primary_circuit);
    println!("{:?}", my_secondary_circuit);   
}
