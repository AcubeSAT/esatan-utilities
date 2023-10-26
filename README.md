## Description

To run the script you're going to need:

- The [Python](https://www.python.org/) programming language
- [Poetry](https://python-poetry.org/docs/#installation) (optional)

To generate a plot (or plots) for your CSV, [clone](https://docs.gitlab.com/ee/gitlab-basics/start-using-git.html#clone-a-repository) this repository, copy or paste the CSV in the repository (`utilities` folder), then:

- Navigate to the `utilites` folder
- If you want to use `poetry` (recommended), do:
    - If it's the first time you're doing this, run `poetry install` in your terminal
    - Run `poetry shell` in your terminal
- If you *don't* want to use `poetry`, do:
    - If it's the first time you're doing this, run `source env/bin/activate` (or `.\env\Scripts\activate` if you're on Windows)
    - Run `python3 -m pip install -r requirements.txt` (it might be `py -m pip install -r requirements.txt` instead if you're on Windows)
- Edit `src/config.toml` and add the filename of your CSV there
- Execute the script by running `python3 src/main.py` (it might be `py src/main.py` if you're on Windows) in your terminal