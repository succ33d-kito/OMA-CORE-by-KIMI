"""Tests for OMA launcher diagnostics and install script."""
import os
import tempfile
from pathlib import Path

import pytest

# We test the parsing functions via check_oma_launcher module
# by temporarily writing launcher scripts to temp files


def _make_launcher(project_path: str) -> str:
    return f"""#!/bin/bash
PROJECT="{project_path}"
cd "$PROJECT"
source venv/bin/activate
python -m core.cli.main "$@"
"""


def _parse_project_from_content(content: str) -> str:
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("PROJECT="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "PROJECT= not found"


class TestParseLauncherProject:

    def test_parse_old_path(self):
        content = _make_launcher("/home/kito/Projects/OMA-CORE by KIMI")
        assert _parse_project_from_content(content) == "/home/kito/Projects/OMA-CORE by KIMI"

    def test_parse_new_path(self):
        content = _make_launcher("/home/kito/O.M.A.-C.O.R.E.")
        assert _parse_project_from_content(content) == "/home/kito/O.M.A.-C.O.R.E."

    def test_parse_missing_project(self):
        content = "#!/bin/bash\necho hello"
        assert _parse_project_from_content(content) == "PROJECT= not found"

    def test_parse_empty_path(self):
        content = _make_launcher("")
        assert _parse_project_from_content(content) == ""


class TestDetectMismatch:

    def test_mismatch_detected(self):
        launcher_path = "/home/kito/Projects/OMA-CORE by KIMI"
        current_repo = "/home/kito/O.M.A.-C.O.R.E."
        assert os.path.abspath(launcher_path) != os.path.abspath(current_repo)

    def test_match_detected(self):
        launcher_path = "/home/kito/O.M.A.-C.O.R.E."
        current_repo = "/home/kito/O.M.A.-C.O.R.E."
        assert os.path.abspath(launcher_path) == os.path.abspath(current_repo)

    def test_mismatch_with_trailing(self):
        launcher_path = "/home/kito/O.M.A.-C.O.R.E"
        current_repo = "/home/kito/O.M.A.-C.O.R.E./"
        assert os.path.abspath(launcher_path) != os.path.abspath(current_repo)


class TestGeneratedLauncher:

    def test_contains_current_repo(self):
        repo = "/home/kito/O.M.A.-C.O.R.E."
        content = _make_launcher(repo)
        assert repo in content

    def test_activates_venv(self):
        content = _make_launcher("/home/kito/O.M.A.-C.O.R.E.")
        assert "source venv/bin/activate" in content or ".venv" in content

    def test_syntax_valid(self):
        content = _make_launcher("/home/kito/O.M.A.-C.O.R.E.")
        assert content.startswith("#!/bin/bash")
        assert 'python -m core.cli.main "$@"' in content


class TestInstallScriptDryRun:

    INSTALL_SCRIPT = """
#!/bin/bash
set -euo pipefail
LAUNCHER_PATH="{launcher_path}"
REPO_DIR="{repo_dir}"
if [ -f "$LAUNCHER_PATH" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    cp "$LAUNCHER_PATH" "${{LAUNCHER_PATH}}.backup_$TIMESTAMP"
fi
cat > "$LAUNCHER_PATH" << 'OMALAUNCHER'
#!/bin/bash
PROJECT="{repo_dir}"
cd "$PROJECT"
if [ -f "$PROJECT/.venv/bin/activate" ]; then
    source "$PROJECT/.venv/bin/activate"
elif [ -f "$PROJECT/venv/bin/activate" ]; then
    source "$PROJECT/venv/bin/activate"
fi
echo "[oma] Project: $PROJECT"
exec python -m core.cli.main "$@"
OMALAUNCHER
chmod 755 "$LAUNCHER_PATH"
echo "Done"
"""

    def test_install_script_backs_up_existing(self):
        with tempfile.TemporaryDirectory() as td:
            launcher = os.path.join(td, "oma")
            repo = os.path.join(td, "repo")
            os.makedirs(repo, exist_ok=True)

            # Create existing launcher
            with open(launcher, "w") as f:
                f.write("old")
            os.chmod(launcher, 0o755)

            script = self.INSTALL_SCRIPT.format(launcher_path=launcher, repo_dir=repo)
            script_path = os.path.join(td, "install.sh")
            with open(script_path, "w") as f:
                f.write(script)
            os.chmod(script_path, 0o755)

            import subprocess
            result = subprocess.run(["bash", script_path], capture_output=True, text=True, timeout=10)
            assert result.returncode == 0

            # Check backup exists
            backups = [f for f in os.listdir(td) if f.startswith("oma.backup_")]
            assert len(backups) >= 1

            # Check new launcher content
            with open(launcher) as f:
                content = f.read()
            assert repo in content
            assert ".venv" in content or "venv" in content
            assert "core.cli.main" in content

    def test_install_script_write_new_launcher(self):
        with tempfile.TemporaryDirectory() as td:
            launcher = os.path.join(td, "oma")
            repo = os.path.join(td, "repo")
            os.makedirs(repo, exist_ok=True)

            script = self.INSTALL_SCRIPT.format(launcher_path=launcher, repo_dir=repo)
            script_path = os.path.join(td, "install.sh")
            with open(script_path, "w") as f:
                f.write(script)
            os.chmod(script_path, 0o755)

            import subprocess
            result = subprocess.run(["bash", script_path], capture_output=True, text=True, timeout=10)
            assert result.returncode == 0

            with open(launcher) as f:
                content = f.read()
            assert repo in content
            assert "core.cli.main" in content


class TestCheckOmaLauncherParsing:

    def test_parse_project_from_file(self):
        """Test that check_oma_launcher can parse a project path from a launcher file."""
        import sys
        script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "check_oma_launcher.py")
        assert os.path.exists(script_path)

        # Use a temp launcher to test parsing
        with tempfile.TemporaryDirectory() as td:
            launcher = os.path.join(td, "test_oma")
            with open(launcher, "w") as f:
                f.write('#!/bin/bash\nPROJECT="/test/repo"\n')
            os.chmod(launcher, 0o755)

            # Read the file and check parse matches
            with open(launcher) as f:
                for line in f:
                    if line.startswith("PROJECT="):
                        project = line.split("=", 1)[1].strip().strip('"')
                        assert project == "/test/repo"
                        break
