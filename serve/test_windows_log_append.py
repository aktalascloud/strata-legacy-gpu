"""Windows inherited-handle regression for #5175; only temporary files and short Python children."""
import ast
import ctypes
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


def opener_from_source():
    tree = ast.parse(Path(__file__).with_name("server.py").read_text(encoding="utf-8-sig"))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "log_opener")
    namespace = {"os": os, "ctypes": ctypes}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "server.py:log_opener", "exec"), namespace)
    return namespace["log_opener"]


@unittest.skipUnless(os.name == "nt", "Windows inherited handle semantics")
class WindowsLogAppend(unittest.TestCase):
    def test_inherited_stdout_stderr_preserve_lines(self):
        opener = opener_from_source()
        child = "import os,sys; os.write(1,(sys.argv[1]+' stdout\\n').encode()); os.write(2,(sys.argv[1]+' stderr\\n').encode())"

        def run(path, engine_append, vision_append):
            path.write_text("previous session\n", encoding="utf-8")
            with open(path, "a", encoding="utf-8", opener=opener if vision_append else None) as vision:
                with open(path, "a", encoding="utf-8", opener=opener if engine_append else None) as engine:
                    engine.write("engine started\n")
                    engine.flush()
                    for handle, label in [(engine, "engine1"), (vision, "vision"), (engine, "engine2")]:
                        subprocess.run([sys.executable, "-c", child, label], stdout=handle, stderr=handle,
                                       check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return path.read_text(encoding="utf-8")

        expected = "previous session\nengine started\nengine1 stdout\nengine1 stderr\nvision stdout\nvision stderr\nengine2 stdout\nengine2 stderr\n"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "shared.log"
            self.assertNotEqual(run(path, False, False), expected)
            self.assertNotEqual(run(path, False, True), expected)
            self.assertEqual(run(path, True, True), expected)

    def test_fd_conversion_failure_closes_owned_handle(self):
        import msvcrt
        from ctypes import wintypes
        opener = opener_from_source()
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        count = kernel.GetProcessHandleCount
        count.argtypes, count.restype = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)), wintypes.BOOL
        process = kernel.GetCurrentProcess
        process.restype = wintypes.HANDLE

        def handles():
            value = wintypes.DWORD()
            self.assertTrue(count(process(), ctypes.byref(value)))
            return value.value

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "conversion.log"
            before = handles()
            with mock.patch.object(msvcrt, "open_osfhandle", side_effect=OSError("fixture conversion failure")):
                with self.assertRaisesRegex(OSError, "fixture conversion failure"):
                    opener(path, os.O_APPEND | os.O_WRONLY)
            self.assertEqual(handles(), before)
            with self.assertRaises(OSError):
                opener(Path(folder) / "missing" / "cannot-open.log", os.O_APPEND | os.O_WRONLY)


if __name__ == "__main__":
    unittest.main()
