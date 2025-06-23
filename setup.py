import sys
from cx_Freeze import setup, Executable

# GUI vs console base
base = "Win32GUI" if sys.platform == "win32" else None

# Include entire folders along with other files
build_exe_options = {
    "packages": ["requests", "packaging"],
    "include_files": [
        "styles.qss",
        "icon.ico",
        "license.rtf",
        "version.json",
        "core/",       # include entire core folder
        "gui/",        # include entire gui folder
        "resources/",  # include entire resources folder
    ],
}

# MSI installer options
bdist_msi_options = {
    "upgrade_code": "{E7CDA630-CB74-4A99-BDB4-F09CB777D3F8}",
    "add_to_path": False,
    "initial_target_dir": r"[ProgramFilesFolder]\Gambit Pairing",
    "install_icon": "icon.ico",
    "launch_on_finish": True,
    "license_file": "license.rtf",
}

executables = [
    Executable(
        script="main.py",
        base=base,
        icon="icon.ico",
        target_name="GambitPairing.exe",
        shortcut_name="Gambit Pairing",
        shortcut_dir="DesktopFolder"
    )
]

setup(
    name="Gambit Pairing",
    version="0.4.0",
    description="Swiss pairing app to streamline tournament management.",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options
    },
    executables=executables
)
