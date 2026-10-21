"""Guard against the on-device NewTerm 3 readInputStream self-sync crash."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = (ROOT / "Common/Controllers/TerminalController.swift").read_text(encoding="utf-8")
SUBPROCESS = (ROOT / "Common/Controllers/SubProcess.swift").read_text(encoding="utf-8")
WORKFLOW = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
ACTION_LABEL_VIEW = (ROOT / "Deps/SwiftUIX/Sources/Intramodular/Control/ActionLabelView.swift").read_text(encoding="utf-8")


class NewTermRootHideQueueTests(unittest.TestCase):
    def test_read_input_only_buffers_without_syncing_to_own_serial_queue(self):
        method = CONTROLLER.split("public func readInputStream(_ data: [UTF8Char])", 1)[1].split(
            "private func readInputStream(_ data: Data)", 1
        )[0]
        self.assertIn("bufferLock.lock()", method)
        self.assertIn("self.readBuffer += data", method)
        self.assertIn("bufferLock.unlock()", method)
        self.assertNotIn("terminalQueue.sync", method)

    def test_error_render_still_uses_nonblocking_queue(self):
        method = CONTROLLER.split("private func updateScreenSize()", 1)[1].split(
            "private func updateTitle()", 1
        )[0]
        self.assertIn("terminalQueue.async", method)
        self.assertIn("self.readInputStream(ColorBars.render", method)
        self.assertIn("@objc private func updateTimerFired()", CONTROLLER)

    def test_passwd_buffer_strings_owned_before_free(self):
        block = SUBPROCESS.split("private static let accountInfo:", 1)[1].split(
            "private static var shell:", 1
        )[0]
        self.assertIn("var result: UnsafeMutablePointer<passwd>? = nil", block)
        self.assertIn("result != nil", block)
        self.assertIn("String(cString: $0)", block)
        self.assertIn("defer { free(raw) }", block)
        self.assertNotIn("return pwd", block)

    def test_hidden_login_spawn_and_resume_do_not_depend_on_resize(self):
        self.assertIn("(Self.login as NSString).utf8String", SUBPROCESS)
        self.assertNotIn("rootfs(Self.login)", SUBPROCESS)
        method = SUBPROCESS.split("func start(initialDirectory:", 1)[1].split(
            "func stop(fromError:", 1
        )[0]
        self.assertLess(method.index("signalSource?.activate()"), method.index("activeProcess()"))
        self.assertIn("if kill(pid, SIGCONT) == 0", SUBPROCESS)

    def test_ci_uses_roothide_theos_and_package_architecture(self):
        self.assertIn("https://github.com/roothide/theos.git", WORKFLOW)
        self.assertIn("ROOTHIDE=1", WORKFLOW)
        self.assertIn("iphoneos-arm64e", WORKFLOW)

    def test_swiftui_button_does_not_recurse_between_action_initializers(self):
        # Hardware: 2026-10-21 16:19:30 NewTerm SIGSEGV stack repeats
        # ActionLabelView.init(action:label:) <-> Button.init(action:label:).
        self.assertIn("public protocol ActionLabelView", ACTION_LABEL_VIEW)
        self.assertIn("extension ActionLabelView", ACTION_LABEL_VIEW)
        self.assertNotIn("extension Button: ActionLabelView", ACTION_LABEL_VIEW)
        self.assertIn("public init(toggle boolean: Binding<Bool>", ACTION_LABEL_VIEW)
        self.assertIn("self.init(action: { boolean.wrappedValue.toggle() }, label: label)", ACTION_LABEL_VIEW)


if __name__ == "__main__":
    unittest.main()
