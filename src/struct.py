# structures.py

# Data structures

_tag_seq = 0

def next_tag():
    """
    Return a new global unique str tag
    """
    global _tag_seq
    tag = f"T{_tag_seq}"
    _tag_seq += 1
    return tag

def reset_tags():
    """
    Reset the tag count restart from T0
    """
    global _tag_seq
    _tag_seq = 0


_issue_seq = 0

def next_issue_num():
    """
    Return incrementing issue-order num
    """
    global _issue_seq
    num = _issue_seq
    _issue_seq += 1
    return num

def reset_issue_seq():
    global _issue_seq
    _issue_seq = 0


# Reservation Station entry (ALU/Branch)
def new_rs():
    """Create an empty reservation-station entry"""
    return {
        "busy":      False,
        "op":        None,
        "tag1":      None,
        "val1":      None,
        "rdy1":      False,
        "tag2":      None,
        "val2":      None,
        "rdy2":      False,
        "dest_tag":  None,
        "issue_num": None,
        "br_target": None,
    }

def clear_rs(rs):
    """
    Reset a reservation-station dict to the empty state
    """
    rs.update(new_rs())

# Load/Store Queue entry
def new_ls():
    """
    Create an empty load/store queue entry
    """
    return {
        "busy":       False,
        "op":         None,
        "base_tag":   None,
        "base_val":   None,
        "base_rdy":   False,
        "imm":        0,
        "data_tag":   None,
        "data_val":   None,
        "data_rdy":   False,
        "dest_tag":   None,
        "issue_num":  None,
        "dest_reg":   None,
    }

def clear_ls(ls):
    """
    Reset a load/store queue dict to the empty state
    """
    ls.update(new_ls())

# Functional-Unit pipeline entry
def new_fu(op, v1, v2, dest_tag, issue_num, latency, br_target=None):
    """
    Create an FU dict representing an ins in exec
    """
    return {
        "op":         op,
        "val1":       v1,
        "val2":       v2,
        "dest_tag":   dest_tag,
        "issue_num":  issue_num,
        "cycles_left": latency,
        "br_target":  br_target,
    }