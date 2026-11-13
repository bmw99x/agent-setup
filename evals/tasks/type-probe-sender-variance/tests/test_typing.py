import subprocess
import sys
from pathlib import Path
from typing import get_type_hints

sys.path.insert(0, "/app")
sys.path.insert(0, str(Path(__file__).parent))
from typecheck_support import APP, check_case, run_mypy  # noqa: E402


def test_project_typechecks_strict_without_ignores():
    result = run_mypy("app", "tests")
    assert result.returncode == 0, result.stdout + result.stderr
    silenced = [str(p) for p in (APP / "app").rglob("*.py") if "type: ignore" in p.read_text()]
    assert not silenced, f"type: ignore in {silenced}"


def test_project_tests_pass():
    result = subprocess.run(["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
                            cwd=APP, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_channel_senders_declare_narrowed_message_param():
    from app.notifications.messages import EmailMessage, SmsMessage
    from app.notifications.senders import EmailSender, SmsSender

    assert get_type_hints(EmailSender.send)["message"] is EmailMessage
    assert get_type_hints(SmsSender.send)["message"] is SmsMessage


def test_matching_sender_and_message_accepted_including_structural_senders():
    """Narrowed implementations must still satisfy the protocol (contravariant param position)."""
    check_case("matching_pairs.py")


def test_mismatched_sender_and_message_rejected():
    """The probe's EXPECT ERROR direction: the checker must enforce the pairing, not just accept everything."""
    check_case("mismatched_pairs.py")
