# ModelSim `.do` 模板

生成位置：`<workspace_root>/sim/sub{x}-{modulename}/scripts/sim.do` 和 `wave.do`。脚本从 `sim/sub{x}-{modulename}/` 运行，RTL fileset 条目相对于 workspace 根。

## `sim.do`

```tcl
quit -sim
if {[file exists work]} { vdel -lib work -all }
vlib work
file mkdir log

set WORKSPACE_ROOT [file normalize "../.."]
set FILESET_HANDLE [open "fileset.f" r]
set VLOG_FILES {}
set VHDL_FILES {}
while {[gets $FILESET_HANDLE line] >= 0} {
    set line [string trim $line]
    if {$line eq "" || [string match "#*" $line]} { continue }
    set source_path [file join $WORKSPACE_ROOT $line]
    if {[regexp -nocase {\.vhd(l)?$} $source_path]} {
        lappend VHDL_FILES $source_path
    } else {
        lappend VLOG_FILES $source_path
    }
}
close $FILESET_HANDLE

if {[llength $VLOG_FILES] > 0} {
    vlog -l log/vlog.log "+incdir+$WORKSPACE_ROOT" {*}$VLOG_FILES
}
if {[llength $VHDL_FILES] > 0} {
    vcom -l log/vcom.log {*}$VHDL_FILES
}
vlog -l log/tb.log tb/tb_<top_module_name>_l1.v
vsim -t ns -voptargs=+acc work.tb_<top_module_name>_l1
run -all
quit -f
```

## `wave.do`

```tcl
view wave
configure wave -signalnamewidth 1
configure wave -timelineunits ns
add wave -noupdate -divider "CLOCK / RESET"
add wave -noupdate -color Yellow /tb_<top_module_name>_l1/<CLK_NAME>
add wave -noupdate -color Red /tb_<top_module_name>_l1/<RST_NAME>
add wave -noupdate -divider "DUT"
add wave -noupdate -expand /tb_<top_module_name>_l1/u_dut/*
run 10us
```

L2 波形和 testbench 必须使用 `tb_<top_module_name>_l2` 层次，不得把 L2 信号混入 L1 结果。
