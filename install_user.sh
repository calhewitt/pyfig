#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

# The local setuptools supports editable installs without downloading build tools.
python3 setup.py develop --user --no-deps

user_bin="$(python3 -m site --user-base)/bin"
fish -c 'fish_add_path --universal $argv[1]' "$user_bin"
fish -c 'contains -- $argv[1] $fish_user_paths' "$user_bin"

printf 'Installed open_pyfig in %s and added it to fish_user_paths.\n' "$user_bin"
