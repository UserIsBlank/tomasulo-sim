# issue.py

# Issue stage

from struct import new_rs, new_ls, next_tag, next_issue_num

def _lookup_reg(name, rt_int, rt_fp):
    """
    Resolve a register operand through the register renamed tables
    Returns value, tag, ready
    """
    if name in ("$0", "R0"):
        return 0, None, True

    if name.startswith("R"):
        entry = rt_int[int(name[1:])]
    elif name.startswith("F"):
        entry = rt_fp[int(name[1:])]
    else:
        return int(name), None, True

    if isinstance(entry, str):
        return None, entry, False
    return entry, None, True

def _parse_mem_operand(token):
    """
    Parse: 'offset(Rn)' → (offset: int, base_reg: str)
    """
    if "(" in token:
        offset = int(token[: token.index("(")])
        base   = token[token.index("(") + 1 : token.index(")")]
        return offset, base
    return int(token), "R0"

def issue(decode_inst, pc_state, labels, rs_pools, ls_queue, rt_int, rt_fp):
    tokens = decode_inst.replace(",", " ").split()
    op = tokens[0].lower()

    # Map opcode to RS pool name
    POOL_MAP = {
        "add": "INT",  "addi": "INT",
        "bne": "BU",
        "fadd": "FPadd",
        "fmul": "FPmult",
        "fdiv": "FPdiv",
        "fld": "LS",   "fsd": "LS",
    }
    pool_name = POOL_MAP[op]

    # Choose correct list of entries
    pool = ls_queue if pool_name == "LS" else rs_pools[pool_name]

    # Find free slot
    free_idx = None
    for i, slot in enumerate(pool):
        if not slot["busy"]:
            free_idx = i
            break
    if free_idx is None:
        return False, "structural"

    tag   = next_tag()
    seqno = next_issue_num()
    slot  = pool[free_idx]

    # Load/Store Phase
    if op in ("fld", "fsd"):
        slot.update(new_ls())
        slot["busy"]      = True
        slot["op"]        = op
        slot["dest_tag"]  = tag
        slot["issue_num"] = seqno

        if op == "fld":
            dest_reg = tokens[1]
            offset, base = _parse_mem_operand(tokens[2])
            slot["imm"]      = offset
            slot["dest_reg"] = dest_reg
            v, t, r = _lookup_reg(base, rt_int, rt_fp)
            slot["base_val"] = v;  slot["base_tag"] = t;  slot["base_rdy"] = r
            slot["data_rdy"] = True
            rt_fp[int(dest_reg[1:])] = tag

        else:
            src_reg = tokens[1]
            offset, base = _parse_mem_operand(tokens[2])
            slot["imm"]      = offset
            slot["dest_reg"] = None
            v, t, r = _lookup_reg(base, rt_int, rt_fp)
            slot["base_val"] = v;  slot["base_tag"] = t;  slot["base_rdy"] = r
            v, t, r = _lookup_reg(src_reg, rt_int, rt_fp)
            slot["data_val"] = v;  slot["data_tag"] = t;  slot["data_rdy"] = r

    # Branch
    elif op == "bne":
        slot.update(new_rs())
        slot["busy"]      = True
        slot["op"]        = op
        slot["dest_tag"]  = tag
        slot["issue_num"] = seqno
        src1, src2, label = tokens[1], tokens[2], tokens[3]
        v, t, r = _lookup_reg(src1, rt_int, rt_fp)
        slot["val1"] = v;  slot["tag1"] = t;  slot["rdy1"] = r
        v, t, r = _lookup_reg(src2, rt_int, rt_fp)
        slot["val2"] = v;  slot["tag2"] = t;  slot["rdy2"] = r
        slot["br_target"] = labels.get(label, 0)
        pc_state["stall"] = True
        pc_state["branch_in_flight"] = True

    # ALU/FP (add, addi, fadd, fmul, fdiv)
    else:
        slot.update(new_rs())
        slot["busy"]      = True
        slot["op"]        = op
        slot["dest_tag"]  = tag
        slot["issue_num"] = seqno
        dest = tokens[1]
        src1 = tokens[2]
        src2 = tokens[3] if len(tokens) > 3 else None

        v, t, r = _lookup_reg(src1, rt_int, rt_fp)
        slot["val1"] = v;  slot["tag1"] = t;  slot["rdy1"] = r

        if src2 is not None:
            try:
                imm = int(src2)
                slot["val2"] = imm; slot["tag2"] = None; slot["rdy2"] = True
            except ValueError:
                v, t, r = _lookup_reg(src2, rt_int, rt_fp)
                slot["val2"] = v;  slot["tag2"] = t;  slot["rdy2"] = r
        else:
            slot["val2"] = 0;  slot["rdy2"] = True

        # Rename destination register
        if dest.startswith("R") and int(dest[1:]) != 0:
            rt_int[int(dest[1:])] = tag
        elif dest.startswith("F"):
            rt_fp[int(dest[1:])] = tag

    return True, None