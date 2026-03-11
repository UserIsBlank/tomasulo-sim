# sim.py

import sys

from conf_parser import read_config, read_program
from struct import (new_rs, new_ls, reset_tags, reset_issue_seq)
from issue import issue
from exec import (advance_fus, collect_finished, compute_result, dispatch_to_fus, dispatch_ls)
from ld_st_unit import lsu_advance, lsu_finished, lsu_complete

def broadcast_cdb(tag, value, rs_pools, ls_queue, rt_int, rt_fp, reg_int, reg_fp):
    """
    Broadcast tag, val on the single Common Data Bus
    """
    # snoop RS pools
    for pool in rs_pools.values():
        for rs in pool:
            if not rs["busy"]:
                continue
            if rs["tag1"] == tag:
                rs["val1"] = value;  rs["rdy1"] = True
            if rs["tag2"] == tag:
                rs["val2"] = value;  rs["rdy2"] = True

    # snoop LS queue
    for ls in ls_queue:
        if not ls["busy"]:
            continue
        if ls["base_tag"] == tag:
            ls["base_val"] = value;  ls["base_rdy"] = True
        if ls["data_tag"] == tag:
            ls["data_val"] = value;  ls["data_rdy"] = True

    # update rt + architectural reg file
    if value is not None:
        for i in range(32):
            if rt_int[i] == tag:
                rt_int[i] = value;  reg_int[i] = value
            if rt_fp[i] == tag:
                rt_fp[i] = value;   reg_fp[i] = value


def main():
    if len(sys.argv) < 2:
        print("Usage: python simulate.py <program_file> [config_file]")
        sys.exit(1)
    prog_file   = sys.argv[1]
    config_file = sys.argv[2] if len(sys.argv) >= 3 else "config.txt"

    # Load config
    cfg = read_config(config_file)
    units   = cfg["units"]
    reg_int = cfg["reg_int"]
    reg_fp  = cfg["reg_fp"]
    memory  = cfg["memory"]

    instructions, labels = read_program(prog_file)

    # Build hardware structures & init state
    reset_tags()
    reset_issue_seq()

    # Reservation-station pools: dict of lists of RS dicts
    rs_pools = {
        "INT":    [new_rs() for _ in range(units["INT"]["rs_count"])],
        "BU":     [new_rs() for _ in range(units["BU"]["rs_count"])],
        "FPadd":  [new_rs() for _ in range(units["FPadd"]["rs_count"])],
        "FPmult": [new_rs() for _ in range(units["FPmult"]["rs_count"])],
        "FPdiv":  [new_rs() for _ in range(units["FPdiv"]["rs_count"])],
    }

    # Load/store queue: list of LS dicts
    ls_queue = [new_ls() for _ in range(units["LS"]["rs_count"])]

    # Functional-unit pipelines: dict of lists
    fu_pipes = {
        "INT":    [],
        "BU":     [],
        "FPadd":  [],
        "FPmult": [],
        "FPdiv":  [],
    }
    fu_ls = []

    # Latency look-up
    latencies = {name: units[name]["latency"] for name in fu_pipes}
    ls_latency = units["LS"]["latency"]

    # Register renamed tables
    rt_int = reg_int[:]
    rt_fp  = reg_fp[:]

    # PC/fetch state
    pc_state = {"pc": 0, "stall": False, "branch_in_flight": False}

    # Decode buffer
    decode_buf = None

    # Statistics
    cycle = 0
    structural_stalls = 0
    MAX_CYCLES = 100_000

    # SIMULATION LOOP
    while cycle < MAX_CYCLES:
        cycle += 1

        # 1. Advance all FU pipelines
        advance_fus(fu_pipes)
        lsu_advance(fu_ls)

        # 2. CDB Arbitration & Writeback
        # Get all FU that finished execution this cycle
        candidates = []

        for name, fu_dict in collect_finished(fu_pipes):
            value = compute_result(fu_dict)
            candidates.append({
                "issue_num": fu_dict["issue_num"],
                "tag":       fu_dict["dest_tag"],
                "value":     value,
                "op":        fu_dict["op"],
                "br_target": fu_dict["br_target"],
                "source":    name,
            })

        if lsu_finished(fu_ls):
            val, dtag, inum, op = lsu_complete(fu_ls, memory)
            candidates.append({
                "issue_num": inum,
                "tag":       dtag,
                "value":     val,
                "op":        op,
                "br_target": None,
                "source":    "LS",
            })

        if candidates:
            # Oldest ins wins CDB access
            winner = min(candidates, key=lambda c: c["issue_num"])

            # Pop the winner from its FU
            if winner["source"] == "LS":
                fu_ls.pop(0)
            else:
                fu_pipes[winner["source"]].pop(0)

            # Resolve branch/broadcast result
            if winner["op"] == "bne":
                taken = (winner["value"] == 1)
                if taken:
                    pc_state["pc"] = winner["br_target"]
                pc_state["stall"] = False
                pc_state["branch_in_flight"] = False

            elif winner["op"] == "fsd":
                pass

            else:
                broadcast_cdb(winner["tag"], winner["value"], rs_pools, ls_queue, rt_int, rt_fp, reg_int, reg_fp)

        # 3. Issue
        if decode_buf is not None:
            issued, reason = issue(decode_buf, pc_state, labels, rs_pools, ls_queue, rt_int, rt_fp)
            if issued:
                decode_buf = None
            elif reason == "structural":
                structural_stalls += 1

        # 4. Dispatch ready RS entries to free FUs
        dispatch_to_fus(fu_pipes, rs_pools, latencies)
        dispatch_ls(fu_ls, ls_queue, ls_latency)

        # 5. Fetch
        if decode_buf is None and not pc_state["stall"]:
            if pc_state["pc"] < len(instructions):
                decode_buf = instructions[pc_state["pc"]]
                pc_state["pc"] += 1

        # Termination check
        all_rs_idle = all(
            not rs["busy"]
            for pool in rs_pools.values() for rs in pool
        )
        all_ls_idle = all(not ls["busy"] for ls in ls_queue)
        all_fu_idle = all(len(pipe) == 0 for pipe in fu_pipes.values())

        if (pc_state["pc"] >= len(instructions)
                and decode_buf is None
                and all_rs_idle and all_ls_idle
                and all_fu_idle and not fu_ls):
            break

    # OUTPUT RESULTS
    print(f"Total Execution Cycles: {cycle}")
    print(f"Structural Stalls: {structural_stalls}")

    print("\nFinal Integer Registers:")
    for i in range(32):
        if reg_int[i] != 0:
            print(f"  R{i} = {reg_int[i]}")

    print("\nFinal FP Registers:")
    for i in range(32):
        if reg_fp[i] != 0.0:
            print(f"  F{i} = {reg_fp[i]}")

    print("\nFinal Memory:")
    for addr in sorted(memory.keys()):
        if memory[addr] != 0.0:
            print(f"  Mem[{addr}] = {memory[addr]}")

if __name__ == "__main__":
    main()