#!/usr/bin/sh
p=$(pwd)/$(dirname $0)
pip install "$p"
cp "$p"/autorotate/icons/disabled.png "$HOME"/.local/share/icons/autorotate.png
cat >"$HOME"/.local/share/applications/autorotate.desktop << EOL
[Desktop Entry]
Encoding=UTF-8
Version=1.0
Type=Application
Terminal=false
Exec=/usr/bin/python -m autorotate.tray
Name=Autorotate
Comment=Tray Icon App to enable auto-rotation
Icon=$HOME/.local/share/icons/autorotate.png
EOL
