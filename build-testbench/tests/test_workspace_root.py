import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from workspace_root import find_workspace_root


def test_find_workspace_root_from_nested_file(tmp_path):
    (tmp_path / ".git").mkdir()
    nested = tmp_path / "rtl" / "module.v"
    nested.parent.mkdir()
    nested.write_text("module module; endmodule\n", encoding="utf-8")

    assert find_workspace_root(nested) == tmp_path


def test_find_workspace_root_keeps_lexical_symlink_path(tmp_path):
    (tmp_path / ".git").mkdir()
    target = tmp_path / "external"
    target.mkdir()
    link = tmp_path / "AlgorithmModule"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        return

    assert find_workspace_root(link / "rtl") == tmp_path
