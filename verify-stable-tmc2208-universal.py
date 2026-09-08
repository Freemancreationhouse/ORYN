from pathlib import Path
import ast

root = Path(__file__).resolve().parent
for rel in ["main.py", "modules/core/pattern_manager.py", "modules/connection/fluidnc_config.py"]:
    ast.parse((root / rel).read_text(encoding="utf-8"), filename=rel)

main = (root / "main.py").read_text(encoding="utf-8")
pm = (root / "modules/core/pattern_manager.py").read_text(encoding="utf-8")
ui = (root / "static/custom/oryn-universal-machine-profile-v7.js").read_text(encoding="utf-8")

assert '"TMC2208": [2, 4, 8, 16]' in main
apply_block = main[main.index('async def apply_machine_hardware_profile'):main.index('class FluidNCCommandRequest')]
assert 'write_setting' not in apply_block
assert 'new_micro / old_micro' not in apply_block
assert 'controller_steps_changed": False' in apply_block
idle = pm.index('await connection_manager.check_idle_async()', pm.index('last planner blocks may still be physically moving'))
hundred = pm.index('state.execution_progress = (total_coordinates, total_coordinates, 0, elapsed_time)', idle)
assert idle < hundred
assert '/api/controller/connect' in main
assert 'TMC2208:[2,4,8,16]' in ui
print('PASS — ORYN stable TMC2208/universal-controller static verification')
