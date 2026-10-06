from bom_monitor_builder.gui import BuilderWindow


class FakeRoot:
    def __init__(self) -> None:
        self.destroy_calls = 0

    def destroy(self) -> None:
        self.destroy_calls += 1


def test_exit_action_destroys_root() -> None:
    window = BuilderWindow.__new__(BuilderWindow)
    window.root = FakeRoot()

    window._exit_application()

    assert window.root.destroy_calls == 1
