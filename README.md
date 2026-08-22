# PyQt OpenModelica Sim-Runner

A desktop GUI application built with Python and PyQt6 that configures and executes a pre-compiled OpenModelica simulation model (`TwoConnectedTanks`).

> Looking to reproduce the model executable itself from source? See [NonInteractingTanks/README.md](./NonInteractingTanks/README.md) for the full OpenModelica/OMEdit compilation walkthrough.

## OpenModelica Runtime & Dependency Findings

### Runtime Dependency Handling
The application relies on the compiled `TwoConnectedTanks` executable and its companion configuration file `TwoConnectedTanks_init.xml`. Both were confirmed as the minimal required runtime set by testing: removing `TwoConnectedTanks_init.xml` causes the executable to fail immediately (`Error: can not read file TwoConnectedTanks_init.xml`); the original `.mo` source files are not required at runtime, only at compile time.

### Excluded File Note (`TwoConnectedTanks_JacA.bin`)
`TwoConnectedTanks_JacA.bin` is intentionally excluded from the shipped `model/` directory.

* **Finding:** Controlled testing (3 trials, toggling only this one file, all other conditions identical) showed a direct, reproducible correlation: including `TwoConnectedTanks_JacA.bin` reliably triggers a division-by-zero assertion (`tank2.Q1 = 0`) at initialization for start times in `[0, 5)`; omitting it allows the simulation to complete cleanly and produce a valid `.mat` result.
* **Hypothesis (unconfirmed):** the model's `tank2.Q1` is defined as `if time <= 5.0 then 0.0 else sqrt(tank1.h)` (see `TwoConnectedTanks_info.json`, equation index 7), and `tank2.T = tank2.V / tank2.Q1` divides by it unconditionally. It's suspected that when `JacA.bin` is present, the solver uses a cached Jacobian sparsity pattern that evaluates this branch at a perturbation point landing exactly on the `Q1 = 0` boundary — whereas without it, the solver recomputes the Jacobian dynamically and avoids that exact point. This mechanism has not been independently confirmed against OpenModelica solver internals.
* **Resolution:** `TwoConnectedTanks_JacA.bin` is not a required runtime file — the executable runs correctly without it (recomputing the Jacobian at a minor performance cost, per its own `debug`-level "could not open sparsity pattern file" warning). It is therefore excluded from `model/` in this repository.

## 🗂️ Repository Structure
* `app.py`: Main PyQt6 Application script
* `model/`: Compiled OpenModelica executable and its required runtime config (`TwoConnectedTanks`, `TwoConnectedTanks_init.xml`)
* `NonInteractingTanks/`: Original Modelica source code (`.mo` files) — not required at runtime, included for reference/reproducibility
* `output/`: Generated simulation results and logs
* `docs/BUILDING.md`: Step-by-step guide to compiling the model from source in OMEdit

## ⚙️ Requirements
* Python 3.6+
* PyQt6 (`pip install PyQt6`)
* Linux OS with OpenModelica installed (required for runtime `.so` libraries — see Developer Notes below)

## 🚀 Usage Instructions

**1. Clone the repository**

Linux / macOS:
```bash
git clone https://github.com/smitpatil06/Sim-Runner
cd Sim-Runner
```

Windows (Command Prompt / PowerShell):
```powershell
git clone https://github.com/smitpatil06/Sim-Runner
cd Sim-Runner
```

**2. Set up a virtual environment and install dependencies**

Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

**3. Run the app**
```bash
python app.py
```

**4.** Click **Select File** and choose the `TwoConnectedTanks` executable in the `model/` folder.

**5.** Enter a **Start Time** and **Stop Time** (integers, `0 <= start < stop < 5`).

**6.** Click **Run Simulation**.

**7.** On completion, console output populates the GUI's terminal pane, and a `.mat` result file plus `simulation_log.txt` are written to `output/`.

![Main window](screenshots/main_window.png)

![Running simulation](screenshots/running_simulation.png)

## 💡 Developer Notes
* **Execution Logic:** The app uses `subprocess.run()` to launch the executable — a blocking call, so the GUI is unresponsive until the simulation completes, after which `stdout`/`stderr` are displayed and logged.
* **Arguments:** Start/stop times are passed as `-startTime=X -stopTime=Y`.
* **Exit Code 255:** `TwoConnectedTanks` returns exit code `255` on successful completion with warnings (e.g., missing sparsity file). `SimulationRunner.run()` explicitly treats `255` as success (with a "completed with warnings" message) to avoid a false failure popup on an otherwise-successful run.
* **OS Dependencies:** The executable dynamically links several OpenModelica-specific libraries (e.g., `libSimulationRuntimeC.so`, the `libsundials_*` family) confirmed via `ldd`. These are not bundled in this repo — OpenModelica must be installed on the target machine (per Step 1 of the task).