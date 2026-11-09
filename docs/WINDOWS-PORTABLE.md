# Windows portable edition

## Laptop par chalana

1. Download **MESSI-Windows-Portable.zip** supplied with the application delivery.
2. Right-click the ZIP and choose **Extract All**. Do not run it from inside the ZIP.
3. Open the extracted **MESSI-Windows** folder.
4. Double-click **START-MESSI.cmd** (Windows may display only START-MESSI).
5. MESSI opens in your existing browser. On first start, Notepad opens your private login details. Copy the email/password to sign in.
6. Keep the MESSI console window open. Close that window to stop the app.

No separate Docker, Python, Node, PostgreSQL or administrator installation is required. The Windows x64 Python runtime and its libraries are bundled. Windows 10/11 x64 and an existing WebGL-capable Chrome/Edge browser are the targets. ARM-native/32-bit Windows is not supported by this package.

Use **SHOW-LOGIN.cmd** if you need to open your login file again. Never share that file. Projects and private credentials are stored under **%LOCALAPPDATA%\MESSI**, outside the extracted program folder. Moving/updating the program folder preserves this data. With MESSI closed, back up the complete data directory to private storage. This is a local laptop edition; it does not provide remote team hosting.

## Build and verification

Maintainers build web assets with npm ci / npm run build, then run `python packaging/windows/build.py`. The builder downloads official CPython 3.13.17 from the Python NuGet distribution, validates its SHA-512 against the official NuGet catalog, and downloads Windows x64 wheels with the application's hash-pinned dependency lock. Windows-specific timezone and colour libraries are pinned and verified using PyPI hashes. No private project databases, machine credentials or network-proxy configuration are included in the ZIP.

The portable launcher uses a local SQLite database and an in-process background planning thread with the same durable job engine. It binds only 127.0.0.1, chooses a local port, sets matching Origin protection, opens the browser after readiness, and uses an OS-backed single-instance lock. Closing the launcher ends the local server/worker; abandoned running-job recovery remains the existing engine's lease behavior.

The build produces a ZIP, its SHA-256 sidecar and BUILD-MANIFEST.json. Archive integrity, runtime/catalog checksums and pinned Windows wheel downloads have been checked. The packaged app's launcher, schedule/export smoke check, compiled SPA and duplicate-instance behavior passed with Linux Python using the identical app files. The existing 35 backend tests passed. This is **not** an executed Windows-native verification claim.

The repository's Windows portable GitHub Actions workflow runs the actual bundled python.exe on a Windows runner before publishing its build artifact. Inspect that run's status separately; a workflow file alone does not establish that it passed. The current cross-built ZIP is not application-code-signed, and physical Windows browser/GPU acceptance remains outstanding. Follow company software policy; do not disable Windows protection or antivirus.
