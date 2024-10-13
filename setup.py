from setuptools import setup

APP = ['app.py']
DATA_FILES = ["key.yaml", "icon.png"]
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'LSUIElement': True,
        'PyRuntimeLocations': [
            '/Users/maruyamatooru/opt/anaconda3/envs/notion/lib/libpython3.12.dylib'
        ]
    },
    'packages': ['rumps'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)