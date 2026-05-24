**Rust reactor Simulation and telemetry API**

This program is designed to simulate the internal temperatures and entropy of a nucelar reactor.

The main reactor logic is stored in lib.rs and the main file spawns several threads for the purposes
of creating external API connections that can be utilized using an external tool.
