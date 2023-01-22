"""This module enables usage such as
python -m packstats

This is needed for standard behaviour compliance
with packages such as pip and other builtins.
"""

from .stats import main_cli


if __name__ == "__main__":
    main_cli()
