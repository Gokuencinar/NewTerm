# NewTerm 3 RootHide rh3fix3: EBADEXEC login fallback

## Observed symptom and original error

On the experimental Dopamine3/RootHide iPhone X iOS 16.7.15 bootstrap,
NewTerm's UI now opens after three auxiliary package installations, but
the first `ie_posix_spawn` of the hidden-root `/usr/bin/login` returns
**EBADEXEC (85), "Bad executable (or shared library)"**. This error occurs
before login invokes `NewTermLoginHelper`, the account shell, or shell
startup scripts. It is not evidence that `.zshrc` is wrong.

## Narrowly scoped application-only fallback

`rh3fix3` attempts the original `login` spawn first, unchanged. If and only
if that spawn returns **EBADEXEC** and the separately signed bundled helper
is executable, NewTerm attempts that helper directly using the same PTY,
environment and suspended spawn attributes. The helper establishes a
controlling TTY, changes directory and execs the selected account shell.

Direct helper launch **does not emulate `login -fp` authentication, account
switching, group/uid changes or root privilege transition**. The terminal
keeps the app's current identity. It is intentionally limited to a
diagnostic workaround for an otherwise unlaunchable login binary. If the
helper or shell also fails, NewTerm keeps the normal error path and logs
the fallback error. Its error is not swallowed.

The helper also fixes a one-byte heap overflow in its shell-path duplicate
that existed in rh3fix2.

## Scope and safety

* No changes to stock rootfs, `/var/jb` links, bootstrap, jailbreak daemon,
  launchd/PID 1, or the original RootHide3 systemhook.
* Do **not** reinstall the r159 "INTERNAL-DEBS-NOT-FOR-INSTALL" files or
  run `arm64epatcher` on additional base packages to attempt this fallback.
* A successful GitHub Actions `.deb` build proves only compilation and
  packaging. Shell execution is not proven until explicitly observed on
  the iPhone. Preserve the previous working NewTerm package for rollback.

## What to record on device

When the app is installed for a test, compare whether the login path still
returns EBADEXEC and whether the fallback succeeds. If it does not, capture
the exact log entry `Bundled login helper also failed` and the errno.
Record the resolved hidden login path, `stat`/`file`/`otool -L`/signature of
that binary and the account shell using **read-only** access. These facts
separate a broken login Mach-O from the RootHide3 spawn/dyld code path.
