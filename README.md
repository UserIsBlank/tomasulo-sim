# Tomasulo Simulator

Authors: \<[Joshua Ha](https://github.com/UserIsBlank)\>

## 1. Introduction
This report describes the design & implementation results of a cycle-accurate simulator for a simplified PowerPc 604 & 620-style CPU that uses Tomasulo’s Algorithm for out-of-order execution. The simulator models a single-issue processor and supports the following eight RISC-V instructions: fld, fsd, add, addi, fadd, fmul, fdiv, and bne. The simulator is implemented in Python 3 and is organized into six source files with clearly separated pipeline stages. All internal states are represented using Python hash maps for transparency and ease of debugging.

## 2. Module Design
The simulator is decomposed into six Python modules with distinct responsibilities:
> * sim.py - Main simulation loop, CDB writeback, command-line interface, output formatting
> * struct.py - Factory functions for all dict-based hardware structures (RS, LS queue, FU entries); global tag and issue-sequence generators
> * conf_parser.py - Parses config.txt (unit parameters, registers, memory) and program .dat files (instructions, labels)
> * issue.py - Issue stage: decodes instruction, looks up/renames operands via the RT, allocates a reservation station or LS queue slot
> * exec.py - Execute stage: advances FU pipelines, collects finished entries, dispatches oldest-ready RS entries to free FUs, computes ALU/FP/branch results
> * ld_st_unit.py - Load/Store Unit: advances the non-pipelined LSU, dispatches ready LS entries, performs memory reads/writes

## 3. Key Data Structures
> * Reservation Station (RS) Entry - Hashmap
> * Load/Store Queue (LS) Entry - Hashmap
> * Functional Unit (FU) Entry - List
> * Register Table - Hashmap
> * Memory - Hashmap
> * Tag & Issue Sequence Generators - Integers

## 4. Benchmark Results
> Total Execution Cycles: 41
> Structural Stalls: 0

> Final Integer Registers:
>   R2 = 100

> Final FP Registers:
>   F0 = 195.0
>   F2 = 12.0
>   F4 = 27.0

> Final Memory:
>   Mem[0] = 111.0
>   Mem[8] = 14.0
>   Mem[16] = 5.0
>   Mem[24] = 10.0
>   Mem[100] = 2.0
>   Mem[108] = 195.0
>   Mem[116] = 63.0
>   Mem[124] = 128.0
>   Mem[200] = 12.0
