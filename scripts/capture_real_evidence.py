"""Capture actual console windows while running the laboratory in WSL."""

from __future__ import annotations

import argparse
import base64
import ctypes
from pathlib import Path
import subprocess
import time

from PIL import ImageGrab
import numpy as np


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "evidence"
STATE = OUTPUT / ".capture_state"
WSL = "Ubuntu-24.04"

CASES = {
    "compile": ("make -s -B all", None),
    "sequential": ("build/nbody_seq 5000 10", ["build/nbody_seq", "5000", "10"]),
    "parallel": ("build/nbody_parallel 5000 10 8 static", ["build/nbody_parallel", "5000", "10", "8", "static"]),
    "optimized": ("build/nbody_optimized 5000 10 8 static", ["build/nbody_optimized", "5000", "10", "8", "static"]),
    "cpp_sequential": ("build/cpp_nbody_seq 5000 10", ["build/cpp_nbody_seq", "5000", "10"]),
    "cpp_parallel": ("build/cpp_nbody_parallel 5000 10 8 static", ["build/cpp_nbody_parallel", "5000", "10", "8", "static"]),
    "cpp_optimized": ("build/cpp_nbody_optimized 5000 10 8 static", ["build/cpp_nbody_optimized", "5000", "10", "8", "static"]),
    "correctness": ("build/compare_full_state 5000 10", None),
    "hardware": ("lscpu", None),
}

user32 = ctypes.windll.user32
user32.GetWindowTextLengthW.argtypes = [ctypes.c_void_p]
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.IsWindowVisible.argtypes = [ctypes.c_void_p]
user32.IsWindowVisible.restype = ctypes.c_int
user32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
user32.SetForegroundWindow.restype = ctypes.c_int


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT)]
user32.GetWindowRect.restype = ctypes.c_int


def find_window(title: str) -> int | None:
    matches: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def visit(hwnd: int, unused: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        size = user32.GetWindowTextLengthW(hwnd)
        if not size:
            return True
        value = ctypes.create_unicode_buffer(size + 1)
        user32.GetWindowTextW(hwnd, value, size + 1)
        if value.value == title:
            matches.append(hwnd)
        return True

    user32.EnumWindows(callback_type(visit), 0)
    return matches[0] if matches else None


def powershell_script(key: str, done: Path) -> str:
    title = f"PCAM_EVIDENCE_{key}"
    caption, arguments = CASES[key]
    lines = [
        f"$Host.UI.RawUI.WindowTitle = '{title}'",
        "[Console]::OutputEncoding = [Text.Encoding]::UTF8",
        "$OutputEncoding = [Text.Encoding]::UTF8",
        "mode con: cols=138 lines=42 | Out-Null",
        f"Set-Location -LiteralPath '{ROOT}'",
        f"Write-Host '$ wsl.exe -d {WSL} -- {caption}' -ForegroundColor Green",
    ]
    if key == "compile":
        lines += [
            f"& wsl.exe -d '{WSL}' -- make -s -B all",
            "$build_status = $LASTEXITCODE",
            "if ($build_status -eq 0) {",
            "    Write-Host 'Compilación completada. Ejecutables generados:'",
            f"    & wsl.exe -d '{WSL}' -- ls -lh build/nbody_seq build/nbody_parallel build/nbody_optimized build/cpp_nbody_seq build/cpp_nbody_parallel build/cpp_nbody_optimized",
            "}",
            "$status = $build_status",
        ]
    elif arguments is not None:
        args = " ".join(f"'{item}'" for item in arguments)
        lines.append(f"& wsl.exe -d '{WSL}' -- {args}")
    elif key == "correctness":
        lines += [
            f"& wsl.exe -d '{WSL}' -- build/compare_full_state 5000 10",
            f"Write-Host '$ wsl.exe -d {WSL} -- build/cpp_compare_full_state 5000 10' -ForegroundColor Green",
            f"& wsl.exe -d '{WSL}' -- build/cpp_compare_full_state 5000 10",
        ]
    else:
        lines += [
            f"& wsl.exe -d '{WSL}' -- lscpu | Select-String -Pattern '^Architecture:|^CPU\\(s\\):|^Model name:|^Thread\\(s\\) per core:|^Core\\(s\\) per socket:|^Socket\\(s\\):'",
            f"Write-Host '$ wsl.exe -d {WSL} -- gcc -dumpfullversion' -ForegroundColor Green",
            f"& wsl.exe -d '{WSL}' -- gcc -dumpfullversion",
            f"Write-Host '$ wsl.exe -d {WSL} -- g++ -dumpfullversion' -ForegroundColor Green",
            f"& wsl.exe -d '{WSL}' -- g++ -dumpfullversion",
        ]
    lines += [
        *([] if key == "compile" else ["$status = $LASTEXITCODE"]),
        "Write-Host ('Exit code: ' + $status)",
        f"[IO.File]::WriteAllText('{done}', [string]$status)",
    ]
    return "\n".join(lines)


def capture(key: str) -> None:
    done = STATE / f"{key}.done"
    done.unlink(missing_ok=True)
    script = powershell_script(key, done)
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    child = subprocess.Popen(
        ["powershell.exe", "-NoLogo", "-NoProfile", "-NoExit", "-EncodedCommand", encoded],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
    title = f"PCAM_EVIDENCE_{key}"
    try:
        limit = time.monotonic() + 120
        hwnd = None
        while time.monotonic() < limit:
            hwnd = find_window(title)
            if hwnd is not None and done.exists():
                break
            if child.poll() is not None:
                raise RuntimeError(f"Console exited before {key} finished")
            time.sleep(0.2)
        else:
            raise TimeoutError(f"Timed out waiting for {key}")
        if done.read_text(encoding="utf-8") != "0":
            raise RuntimeError(f"Command {key} failed; inspect the visible console")
        focused = user32.SetForegroundWindow(hwnd)
        time.sleep(0.5)
        rect = RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            raise RuntimeError(f"Cannot locate the console window for {key}")
        screenshot = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
        if screenshot.getextrema() == ((0, 0), (0, 0), (0, 0)):
            raise RuntimeError(f"The console window for {key} is blank (focused={focused})")
        # Crop only the terminal viewport. The title bar contains unrelated tabs;
        # the bottom of the window contains unused terminal background.
        top = 108
        pixels = np.asarray(screenshot.convert("RGB"))
        viewport = pixels[top:, :, :].astype(np.int16)
        white = np.all(viewport > 185, axis=2)
        green = ((viewport[:, :, 1] > 110) &
                 (viewport[:, :, 1] > viewport[:, :, 0] + 20) &
                 (viewport[:, :, 1] > viewport[:, :, 2] + 20))
        rows, columns = np.nonzero(white | green)
        if len(rows) < 50:
            raise RuntimeError(f"No readable terminal output was captured for {key}")
        bottom = min(screenshot.height, top + int(rows.max()) + 24)
        right = min(screenshot.width, max(700, int(columns.max()) + 42))
        screenshot = screenshot.crop((7, top, right, bottom))
        target = OUTPUT / f"{key}.png"
        screenshot.save(target)
        print(f"Saved real console capture: {target} ({screenshot.width}x{screenshot.height})")
    finally:
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
        done.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=CASES)
    args = parser.parse_args()
    STATE.mkdir(exist_ok=True)
    for key in [args.only] if args.only else CASES:
        capture(key)
    STATE.rmdir()


if __name__ == "__main__":
    main()
