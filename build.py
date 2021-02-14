import PyInstaller.__main__

PyInstaller.__main__.run(
    [
        "main.py",
        "--onefile",
        "--console",
        "--icon=small_logo.ico",
        "--distpath=./",
        "--hiddenimport=uvicorn.logging",
        "--hiddenimport=uvicorn.loops",
        "--hiddenimport=uvicorn.loops.auto",
        "--hiddenimport=uvicorn.protocols",
        "--hiddenimport=uvicorn.protocols.http",
        "--hiddenimport=uvicorn.protocols.http.auto",
        "--hiddenimport=uvicorn.protocols.websockets",
        "--hiddenimport=uvicorn.protocols.websockets.auto",
        "--hiddenimport=uvicorn.lifespan",
        "--hiddenimport=uvicorn.lifespan.on",
    ]
)
