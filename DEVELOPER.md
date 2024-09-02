# zoozl developer documentation

Meant for developers who want to contribute to zoozl project.

## Dev environment

Install dev environment
```bash
python -m venv env
env/bin/pip install -r requirements-dev.txt
```

Automate the precommit steps like running tests before commiting code.
```bash
cd .git/hooks/ && ln -s ../../scripts/pre-commit . && cd -
```

