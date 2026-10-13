#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

user_bin="$(python3 -m site --user-base)/bin"
launcher="$user_bin/open_pyfig"
if [[ ! -x "$launcher" ]]; then
    ./install_user.sh
fi

data_home="${XDG_DATA_HOME:-$HOME/.local/share}"
config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
mime_dir="$data_home/mime"
applications_dir="$data_home/applications"
desktop_file="$applications_dir/pyfig-open.desktop"
icon_theme_dir="$data_home/icons/hicolor"
icon_dir="$icon_theme_dir/scalable/mimetypes"

mkdir -p "$mime_dir/packages" "$applications_dir" "$icon_dir" "$config_home"
install -m 0644 desktop/pyfig.xml "$mime_dir/packages/pyfig.xml"
update-mime-database "$mime_dir"
install -m 0644 desktop/application-x-pyfig.svg "$icon_dir/application-x-pyfig.svg"
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$icon_theme_dir"
fi

printf '%s\n' \
    '[Desktop Entry]' \
    'Type=Application' \
    'Name=Pyfig Figure Viewer' \
    'Comment=Open an editable Matplotlib figure' \
    'Icon=application-x-pyfig' \
    "Exec=$launcher %f" \
    "TryExec=$launcher" \
    'MimeType=application/x-pyfig;' \
    'Terminal=false' \
    'NoDisplay=true' \
    'Categories=Graphics;' > "$desktop_file"

desktop-file-validate "$desktop_file"
update-desktop-database "$applications_dir"
xdg-mime default pyfig-open.desktop application/x-pyfig

if [[ "$(xdg-mime query default application/x-pyfig)" != 'pyfig-open.desktop' ]]; then
    echo 'Could not set pyfig-open.desktop as the default .pyfig handler.' >&2
    exit 1
fi

echo 'Nautilus will open .pyfig files with open_pyfig.'
