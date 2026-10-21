"""Contract for the isolated NewTerm RootHide EBADEXEC startup fallback.

This is a structural test; a macOS workflow is required to compile, and an
iPhone is required to prove that its login/helper/shell can actually spawn.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
SWIFT = (ROOT / "Common/Controllers/SubProcess.swift").read_text(encoding="utf-8")
HELPER = (ROOT / "NewTermLoginHelper/main.c").read_text(encoding="utf-8")
CONTROL = (ROOT / "control").read_text(encoding="utf-8")
WORKFLOW = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")


class RootHideLoginHelperFallbackTests(unittest.TestCase):
    def test_original_login_has_priority(self):
        original = SWIFT.index("var result = ie_posix_spawn(&pid, (Self.login as NSString).utf8String")
        fallback = SWIFT.index("if result == EBADEXEC && !Self.loginIsShell")
        self.assertLess(original, fallback)
        self.assertIn("FileManager.default.isExecutableFile(atPath: Self.loginHelper)", SWIFT)
        self.assertIn('let fallbackArgv = ["-NewTermLoginHelper", initialDirectory ?? Self.homeDirectory, Self.shell].cStringArray', SWIFT)
        self.assertIn("result = ie_posix_spawn(&pid, (Self.loginHelper as NSString).utf8String", SWIFT)
        self.assertIn("pid = pid_t()", SWIFT)
        self.assertIn("defer { fallbackArgv.deallocate() }", SWIFT)

    def test_fallback_preserves_pty_and_existing_spawn_flags(self):
        spawn = SWIFT[SWIFT.index("var result = ie_posix_spawn"):SWIFT.index("close(fds.replica)")]
        self.assertEqual(spawn.count("ie_posix_spawn(&pid"), 2)
        self.assertNotIn("posix_spawnattr_setflags", spawn)
        self.assertNotIn("setuid(", spawn)
        self.assertNotIn("setgid(", spawn)
        self.assertNotIn("system(", spawn)
        self.assertIn("&actions, &attr, fallbackArgv, envp", spawn)
        self.assertIn("if result == 0", spawn)
        # A still failing fallback must retain the normal error UI.
        self.assertIn("if result != 0", SWIFT[SWIFT.index("close(fds.replica)"):])
        self.assertIn("SubProcessIllegalStateError.forkFailed(errno: result)", SWIFT)

    def test_helper_controls_tty_execs_shell_and_no_heap_overflow(self):
        self.assertIn('strcmp(argv[0], "-NewTermLoginHelper")', HELPER)
        for expected in ("setsid()", "TIOCSCTTY", "chdir(argv[1])", "strdup(argv[2])",
                         'asprintf(&loginArg0, "-%s", basename(program))',
                         "execvp(program, (char **)&argv[2])", "free(loginArg0)",
                         "free(program)"):
            with self.subTest(expected=expected):
                self.assertIn(expected, HELPER)
        self.assertNotIn("malloc(strlen(argv[2]))", HELPER)

    def test_new_package_is_distinct_and_builds_root_hide_scheme(self):
        self.assertIn("Version: 3.0~beta1+rh3fix3", CONTROL)
        self.assertIn("ROOTHIDE=1", WORKFLOW)
        self.assertIn("test \"$(dpkg-deb -f", WORKFLOW)
        self.assertIn("NewTerm3-RootHide-rh3fix3-login-helper-fallback", WORKFLOW)
        self.assertIn("TARGET_CODESIGN", (ROOT / "Makefile").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
