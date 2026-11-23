#!/usr/bin/env python3
"""Make the Judge Smile — make.fun entry.

Writes one line (at most 200 characters) about a small good thing that
happened today to /output/entry.txt (or $MAKEFUN_OUTPUT_DIR/entry.txt).
Pure Python standard library only; no network, no reads outside this repo.
"""

import os
import stat
import sys
import tempfile

LINE = (
    "At 7:40 the bus driver held the doors while I sprinted across the "
    "road, then grinned: 'We've all been the late one' \u2014 and the whole "
    "bus nodded along, like we'd all just been let off the hook."
)


def main() -> int:
    line = LINE

    # Validate: 1-200 characters, not only whitespace.
    if not line or not line.strip():
        print("error: entry line is empty or only whitespace", file=sys.stderr)
        return 1
    if len(line) > 200:
        print(
            "error: entry line is %d characters, over the 200 limit" % len(line),
            file=sys.stderr,
        )
        return 1

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        print("error: cannot create output dir %r: %s" % (out_dir, exc),
              file=sys.stderr)
        return 1

    target = os.path.join(out_dir, "entry.txt")
    data = line.encode("utf-8")

    # Write via a temp file in the same directory, then atomically replace.
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=out_dir, prefix=".entry-", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            os.chmod(tmp_path, 0o644)
            os.replace(tmp_path, target)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except OSError as exc:
        print("error: cannot write %r: %s" % (target, exc), file=sys.stderr)
        return 1

    # Read back and verify bytes and mode.
    try:
        with open(target, "rb") as fh:
            actual = fh.read()
        mode = stat.S_IMODE(os.stat(target).st_mode)
    except OSError as exc:
        print("error: cannot verify %r: %s" % (target, exc), file=sys.stderr)
        return 1

    if actual != data:
        print("error: read-back bytes differ from entry line", file=sys.stderr)
        return 1
    if mode != 0o644:
        print("error: output mode is %04o, expected 0644" % mode, file=sys.stderr)
        return 1

    print("wrote %s (%d characters, mode 0644)" % (target, len(line)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
