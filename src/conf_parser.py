# conf_parser.py

def read_config(filepath):
    """
    Parse config.txt and return dict
    """
    with open(filepath, "r") as fh:
        lines = [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]

    unit_names = ["INT", "FPadd", "FPmult", "FPdiv", "BU", "LS"]
    units = {}
    for i, name in enumerate(unit_names):
        rs_count, latency = lines[i].split()
        units[name] = {"rs_count": int(rs_count), "latency": int(latency)}

    # Registers
    reg_int = [0] * 32
    reg_fp  = [0.0] * 32
    for token in lines[6].split(","):
        token = token.strip()
        if token.startswith("R"):
            idx, val = token[1:].split("=")
            reg_int[int(idx)] = int(val)
        elif token.startswith("F"):
            idx, val = token[1:].split("=")
            reg_fp[int(idx)] = float(val)

    # Memory
    memory = {}
    if len(lines) > 7:
        for token in lines[7].split(","):
            token = token.strip()
            if "=" in token:
                addr, val = token.split("=")
                memory[int(addr.strip())] = float(val.strip())

    return {
        "units":   units,
        "reg_int": reg_int,
        "reg_fp":  reg_fp,
        "memory":  memory,
    }

def read_program(filepath):
    """
    Parse a RISC-V assembly file
    Returns ins & labels dict
    """
    instructions = []
    labels = {}
    with open(filepath, "r") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("%") or line.startswith("#"):
                continue
            first = line.split()[0]
            if first.endswith(":"):
                labels[first[:-1]] = len(instructions)
                line = line[len(first):].strip()
            if line:
                instructions.append(line)
    return instructions, labels