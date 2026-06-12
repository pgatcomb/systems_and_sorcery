# Rusty Overlord Settlement Simulator

This project is designed to be a tabletop settlement simulator where players can interact with a virtual settlement using a webpage from a server hosted by the gamemaster.

## Concepts

A settlement consists of:
* Settlers - Each with age, health, skills [split between work, research and building], resource affinities and aversions
* Buildings - Each of these represents a single unit that consumes, produces and/or stores a resource.
* Technologies - These act as 'gates' to available buildings, e.g. you must research a specific tech to be able to build a specific building
* Resources - These are the 'materials' that are consumed, produced, traded and stored.  These resources can be physical, e.g. water or roleplay specific such as 'morale' or 'hope'.

## Initialization/Startup

### Rust Engine/Server
When you first start the settlement server, it will begin by searching for the gamestate.json stored in the game folder. If it finds this file, it will load that data directly into the engine and then perform a validation against the data stored in the /gamedata/ folder.

If this file *is not* present, the program automatically parses and validates the data in the /gamedata/ folder and generates the default gamestate.json.

With the data validated, the engine spools up an API allowing the client to connect to it to make their adjustments through PUT and GET calls.

### Client/React Server and Client

After the engine is running, the client should be started. This spools up a adaptable webpage that players can access with their mobile devices to view the status of the settlement, put in various requests and, if the player logs in with ADMIN, can commit the changes and execute the turn processing before returning the new states to all the connected clients.

The client consists of:
* A login page
* A status page with broad settlement information, this is also where the COMMIT button lives for the gamemaster to run the day/year/season/tick
* A building page where new buildings can be ordered, razed, etc.
* A tech page where techs can be researched and viewed
* A settler/colonist page where players can see all their colonists along with being able to assign their activity preference/priorities/bias to Auto, build, research, work, rest. This also reveals specific abilities, aversions, affinities and skills to each colonist.
* A resources page where the players can view their total production, consumption, maximum storage and stockpile
* An events page that shows all the events triggered so far as defined in the events file so players can understand the 'meta' so far.

### Turn Commit

As players make adjustments and orders, a mutable working copy of the gamestate is maintained on the Rust server.
When the gamemaster engages the turn/tick, the engine performs the following steps:

1. Clone the current working gamestate into a snapshot for simulation.
2. Determine colonist task assignments based on skills, affinities, aversions and any player-provided preferences.
3. Calculate total production and consumption across all systems (buildings, colonists, etc.).
4. Resolve resource changes, applying storage limits and capacity constraints.
5. Advance building construction progress and update building states.
6. Advance research progress and update the technology tree.
7. Trigger and resolve events based on current conditions.
8. Update colonist states (health, fatigue, etc.) based on activity outcomes.
9. Replace the working gamestate with the newly generated state.
10. Persist the updated gamestate to disk.
11. Increment the turn counter and advance the game timeline.

## Data-Driven Design

The Rust engine operates entirely on numeric identifiers and does not contain any hardcoded definitions for settlers, buildings, technologies or resources.
All descriptive and behavioral data is loaded from external JSON files located in the `/gamedata/` directory at startup. This includes:

* Building definitions (costs, production, storage)
* Technology definitions (requirements, unlocks)
* Resource definitions (names, types)
* Starting settlers and their stats

The engine uses these definitions to interpret numeric references stored in the game state.

This allows:
* Flexible content updates without recompiling the engine
* Easy rebalancing of systems
* Potential for modding or alternate scenarios

## Design Principles

This project follows several core principles:

* Data-driven design – All content is defined externally and loaded at runtime.
* Deterministic simulation – Each turn produces a predictable outcome based solely on the input state, modified by events.
* Separation of concerns – The backend handles simulation, while the client handles presentation.
* Mobile-first interaction – The user interface is designed for simple, touch-based interaction but is perfectly fine on desktop devices, etc.
* Player intent over micromanagement – Players influence the system through priorities rather than direct control.