# Sidekick
 
Aputomates gym processes .

## Project Architecture

    ├── LICENSE
    │
    ├── .env               <- Environment variables used in project.
    │
    ├── Makefile           <- Makefile with shortcut commands (e.g. environment setup, testing).
    │
    ├── README.md          <- The top-level README for users/developers of this project.
    │
    ├── data
    │   └── sample         <- Sample data for which experiments can be executed on.
    │
    ├── requirements.txt   <- Requirements file for reproducing the analysis environment
    │
    ├── research           <- Notebooks for function development
    │
    ├── setup.py           <- Setup file making `src` importable (pip install -e .) 
    │
    ├── tests              <- Tests for `sidekick`
    │
    └── sidekick           <- Flask app
        ├── static         <- Custom CSS & JS
        └── templates      <- Jinja templates

## Getting Started

### Prerequisites

This project requires:

* [GNU Make](https://www.gnu.org/software/make/) (symlink: `make`)
* [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli#download-and-install) (symlink: `heroku`)
* [Python3.8 or above](https://www.python.org/downloads/) (symlink: `python`)
* pip - installed with Python3 (symlink: `pip`)
* [PostgreSQL 12](https://www.postgresql.org/download) (symlink: `psql`)

### Installing

On Mac/Linux, run `make pyenv` in order to set up the virtual environment for this project. If on
Windows, run `make win-pyenv`.

You can then activate the environment by executing `source venv/bin/activate` (Mac/Linux) or 
`source venv/scripts/activate` (Windows + Git Bash).

### Development

Export `FLASK_APP=sidekik` and `FLASK_ENV=development` to successfully run the app in development
mode. You can also add both of the above environment variables to a `.env` file to skip repeating
this step.

## Running Tests

Run `make tests` in order to execute the unit tests (found in `tests`).

## Contributors

* **Mitchell Murphy**
    * Maintainer

Contributors are advised to follow [PEP 8 guidelines](https://www.python.org/dev/peps/pep-0008/) for 
code layout.

Outstanding issues (tasks, bugs, etc.) can be found in the Issues tracker. Log any completed issues 
in the contributors list above.
