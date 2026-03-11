# tomasulo-sim

1. Introduction
This report describes the design & implementation results of a cycle-accurate simulator for a simplified PowerPc 604 & 620-style CPU that uses Tomasulo’s Algorithm for out-of-order execution. The simulator models a single-issue processor and supports the following eight RISC-V instructions: fld, fsd, add, addi, fadd, fmul, fdiv, and bne.
The simulator is implemented in Python 3 and is organized into six source files with clearly separated pipeline stages. All internal states are represented using Python hash maps for transparency and ease of debugging.

2. Module Design
The simulator is decomposed into six Python modules with distinct responsibilities:
Module
Responsibility
sim.py
Main simulation loop, CDB writeback, command-line interface, output formatting
struct.py
Factory functions for all dict-based hardware structures (RS, LS queue, FU entries); global tag and issue-sequence generators
conf_parser.py
Parses config.txt (unit parameters, registers, memory) and program .dat files (instructions, labels)
issue.py
Issue stage: decodes instruction, looks up/renames operands via the RT, allocates a reservation station or LS queue slot
exec.py
Execute stage: advances FU pipelines, collects finished entries, dispatches oldest-ready RS entries to free FUs, computes ALU/FP/branch results
ld_st_unit.py
Load/Store Unit: advances the non-pipelined LSU, dispatches ready LS entries, performs memory reads/writes

3. Key Data Structures
Reservation Station (RS) Entry - Hashmap
Load/Store Queue (LS) Entry - Hashmap
Functional Unit (FU) Entry - List
Register Table - Hashmap
Memory - Hashmap
Tag and Issue Sequence Generators - Integers

4. Benchmark Results
