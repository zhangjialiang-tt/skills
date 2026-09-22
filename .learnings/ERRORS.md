# Errors

## [ERR-20260911-COCOTB-SCALAR-LOGIC] cocotb 2.1 scalar resolve check

**Status**: resolved  
**Area**: tests  

### Summary
Generated smoke used `.value.integer` for a 1-bit scalar; cocotb 2.1 exposes scalar values as `Logic`, which has no `.integer`.

### Evidence
A synthetic generated Icarus smoke failed with `AttributeError: 'Logic' object has no attribute 'integer'`.

### Resolution
Use `.value.is_resolvable` for X/Z checks; read `.integer` only for resolved multi-bit `LogicArray` values and `.to_signed()` for signed arrays. Updated `cocotb-testbench/scripts/gen_cocotb_skeleton.py` and troubleshooting/API references. Synthetic smoke then passed.
