# exec.py

# Execute stage

from struct import new_fu, clear_rs

def compute_result(fu):
    """
    Return num result produced by completed FU dict
    """
    op = fu["op"]
    v1, v2 = fu["val1"], fu["val2"]
    if op in ("add", "addi"):
        return int(v1) + int(v2)
    if op == "fadd":
        return float(v1) + float(v2)
    if op == "fmul":
        return float(v1) * float(v2)
    if op == "fdiv":
        return float(v1) / float(v2) if v2 != 0 else 0.0
    if op == "bne":
        return 1 if v1 != v2 else 0
    return 0

def advance_fus(fu_pipes):
    """
    Decrement cycles_left for every in-flight FU entry
    """
    for pipe in fu_pipes.values():
        if pipe and pipe[0]["cycles_left"] > 0:
            pipe[0]["cycles_left"] -= 1

def collect_finished(fu_pipes):
    """
    Return list of unit_name, fu_dict for every FU whose cycles_left == 0
    """
    ready = []
    for name, pipe in fu_pipes.items():
        if pipe and pipe[0]["cycles_left"] == 0:
            ready.append((name, pipe[0]))
    return ready

def _oldest_ready_rs(pool):
    """
    Return idx of oldest ready entry in an RS pool list or None
    """
    best_idx = None
    best_seq = None
    for i, rs in enumerate(pool):
        if rs["busy"] and rs["rdy1"] and rs["rdy2"]:
            if best_seq is None or rs["issue_num"] < best_seq:
                best_idx = i
                best_seq = rs["issue_num"]
    return best_idx

def dispatch_to_fus(fu_pipes, rs_pools, latencies):
    """
    For each functional unit that is free, dispatch the oldest ready ins from reservation-station pool
    """
    for name in ("INT", "BU", "FPadd", "FPmult", "FPdiv"):
        pipe = fu_pipes[name]
        if pipe:
            continue
        pool = rs_pools[name]
        idx  = _oldest_ready_rs(pool)
        if idx is None:
            continue
        rs = pool[idx]
        fu = new_fu(
            op        = rs["op"],
            v1        = rs["val1"],
            v2        = rs["val2"],
            dest_tag  = rs["dest_tag"],
            issue_num = rs["issue_num"],
            latency   = latencies[name],
            br_target = rs.get("br_target"),
        )
        pipe.append(fu)
        clear_rs(rs)

def _oldest_ready_ls(queue):
    """
    Return idx of oldest ready LS entry or None
    """
    best_idx = None
    best_seq = None
    for i, ls in enumerate(queue):
        if not ls["busy"]:
            continue
        if not ls["base_rdy"]:
            continue
        if ls["op"] == "fsd" and not ls["data_rdy"]:
            continue
        if best_seq is None or ls["issue_num"] < best_seq:
            best_idx = i
            best_seq = ls["issue_num"]
    return best_idx

def dispatch_ls(fu_ls, ls_queue, ls_latency):
    """
    Dispatch oldest ready LS entry if load/store unit is free
    """
    if fu_ls:
        return
    idx = _oldest_ready_ls(ls_queue)
    if idx is None:
        return
    ls = ls_queue[idx]
    address = int(ls["base_val"]) + ls["imm"]
    lsu = {
        "op":         ls["op"],
        "address":    address,
        "data":       ls["data_val"] if ls["op"] == "fsd" else None,
        "dest_tag":   ls["dest_tag"],
        "dest_reg":   ls["dest_reg"],
        "issue_num":  ls["issue_num"],
        "cycles_left": ls_latency,
    }
    fu_ls.append(lsu)
    
    from struct import clear_ls
    clear_ls(ls)