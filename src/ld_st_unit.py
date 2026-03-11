# ld_st_unit.py

# Load/Store execution unit

def lsu_advance(fu_ls):
    """
    Advance load/store unit by decrementing cycles_left
    """
    if fu_ls and fu_ls[0]["cycles_left"] > 0:
        fu_ls[0]["cycles_left"] -= 1


def lsu_finished(fu_ls):
    """
    Return true if the LSU has a completed ins
    """
    return bool(fu_ls) and fu_ls[0]["cycles_left"] == 0


def lsu_complete(fu_ls, memory):
    """
    Perform the memory access for the completed LSU entry
    Returns value, dest_tag, issue_num, op
    """
    entry = fu_ls[0]
    if entry["op"] == "fld":
        value = memory.get(entry["address"], 0.0)
    else:
        memory[entry["address"]] = entry["data"]
        value = None
    return value, entry["dest_tag"], entry["issue_num"], entry["op"]