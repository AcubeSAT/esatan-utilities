<div align="center">
<p>
    <a href="https://gitlab.com/acubesat/documentation/cdr-public/-/blob/master/DDJF/DDJF_THR.pdf?expanded=true&viewer=rich">DDJF_PL 📚🧪</a> &bull;
    <a href="https://spacedot.gr/">SpaceDot 🌌🪐</a> &bull;
    <a href="https://acubesat.spacedot.gr/">AcubeSAT 🛰️🌎</a>
</p>
</div>

## Description

A repository to host code and a bunch of other stuff.
Various utilities in script form for interfacing and working with ESATAN-TMS.

- [Description](#description)
- [CSV Parse/Plot](#csv-parseplot)
  - [Usage](#usage)
    - [End User](#end-user)
    - [Developer](#developer)
  - [File Structure](#file-structure)
  - [CI](#ci)

## CSV Parse/Plot

### Usage

#### End User

Grab the binary from the [releases](https://github.com/AcubeSAT/esatan-utilities/releases/tag/v0.1.0-alpha) page.
Make sure that the `.zip` you selected is appropriate for your platform, e.g., `windows.zip`.
Extract the archive, **navigate to the `main` directory**, and start the `main` executable.

#### Developer

Grab the repository, and make sure you have python and [poetry](https://python-poetry.org/docs/) installed.
- `poetry lock`
- `poetry install --no-root -E build -E format` (`build` installs the dependencies needed for building the bundle, `format` installs the dependencies needed for `yapf`)
- make sure to activate the poetry environment, by sourcing the appropriate `activate` script, e.g. `activate.ps1` for Powershell, located in `.venv/Scripts/`
- for an example on how to build and format, take a look at `.github/workflows/ci.yml`

<details>
<summary>Beginner-friendly details</summary>

To run the script you're going to need:

- The [Python](https://www.python.org/) programming language
- [Poetry](https://python-poetry.org/docs/#installation) (optional)

- Navigate to the `utilites` folder
- If you want to use `poetry` (recommended), do:
    - If it's the first time you're doing this, run `poetry install` in your terminal
    - Run `poetry shell` in your terminal
- If you *don't* want to use `poetry`, do:
    - If it's the first time you're doing this, run `source env/bin/activate` (or `.\env\Scripts\activate` if you're on Windows)
    - Run `python3 -m pip install -r requirements.txt` (it might be `py -m pip install -r requirements.txt` instead if you're on Windows)
- Execute the script by running `python3 src/main.py` (it might be `py src/main.py` if you're on Windows) in your terminal

</details>

### File Structure

<details>
<summary>Click to expand</summary>

```graphql
./.github/workflows
└─ ci.yml
.gitlab-ci.yml
./src/
├─ config_model.py
├─ config.toml
├─ eltypes.py
├─ GCodeUtils.py
├─ GUI.py
├─ IOUtils.py
├─ main.py
├─ parse.py
├─ paths.py
└─ plot.py
.editorconfig
add-files-to-spec
example.csv
poetry.lock
poetry.toml
pyproject.toml
requirements.txt
```

### CI

All [CI magic](https://github.com/AcubeSAT/esatan-utilities/actions/workflows/ci.yml) happens using [GitHub Actions](https://docs.github.com/en/actions).
The related configuration is all located within `.github/workflows/ci.yml`:

<details>
<summary>Click to expand</summary>

```yaml
name: CI
run-name: ${{ github.actor }} is running 🚀
on: [push]

jobs:
  ci:
    strategy:
      fail-fast: false # Don't fail all jobs if a single job fails.
      matrix:
        python-version: ["3.11"]
        poetry-version: ["1.2.2"] # Poetry is used for project/dependency management.
        os: [ubuntu-latest, macos-latest, windows-latest]
        include: # Where pip stores its cache is OS-dependent.
          - pip-cache-path: ~/.cache
            os: ubuntu-latest
          - pip-cache-path: ~/.cache
            os: macos-latest
          - pip-cache-path: ~\appdata\local\pip\cache
            os: windows-latest
    defaults:
      run:
        shell: bash # For sane consistent scripting throughout.
    runs-on: ${{ matrix.os }}
    steps:
      - name: Check out repository
        uses: actions/checkout@v3
      - name: Setup Python
        id: setup-python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: ${{ matrix.poetry-version }}
          virtualenvs-create: true
          virtualenvs-in-project: true # Otherwise the venv will be the same across all OSes.
          installer-parallel: true
      - name: Load cached venv
        id: cached-pip-wheels
        uses: actions/cache@v3
        with:
          path: ${{ matrix.pip-cache-path }}
          key: venv-${{ runner.os }}-${{ steps.setup-python.outputs.python-version }}-${{ hashFiles('**/poetry.lock') }}
      - name: Install dependencies
        run: poetry install --no-interaction --no-root -E build -E format # https://github.com/python-poetry/poetry/issues/1227
      - name: Check formatting
        run: |
          source $VENV
          yapf -drp --no-local-style --style "facebook" src/
      - name: Build for ${{ matrix.os }}
        run: | # https://stackoverflow.com/questions/19456518/error-when-using-sed-with-find-command-on-os-x-invalid-command-code
          source $VENV
          pyi-makespec src/main.py
          if [ "$RUNNER_OS" == "macOS" ]; then
            sed -i '' -e '2 r add-files-to-spec' main.spec
            sed -i '' -e 's/datas=\[]/datas=added_files/' main.spec
          else
            sed -i '2 r add-files-to-spec' main.spec
            sed -i 's/datas=\[]/datas=added_files/' main.spec
          fi
          pyinstaller main.spec
      - name: Archive binary artifacts
        uses: actions/upload-artifact@v3
        with:
          name: ${{ matrix.os }}-bundle
          path: dist
```

</details>

On each push, the application is bundled into a single folder containing an executable, for each OS.
This happens using [`pyinstaller`](https://www.pyinstaller.org/).
First there's a formatting check using [`yapf`](https://github.com/google/yapf).
Then, the application is built.
Everything is cached when possible.
If the job terminates successfully, the bundle folder for each OS is uploaded as an artifact that the user can download, instead of having to run `pyinstaller` locally, or having to install `python` and the project dependencies locally through `poetry`.
