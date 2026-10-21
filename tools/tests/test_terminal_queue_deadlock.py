"""Guard against the on-device NewTerm 3 readInputStream self-sync crash."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = (ROOT / "Common/Controllers/TerminalController.swift").read_text(encoding="utf-8")


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


if __name__ == "__main__":
    unittest.main()
