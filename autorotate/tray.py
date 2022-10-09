#!/usr/bin/env python
import subprocess
from importlib import resources
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon


def icon_activated(reason):
    if reason == QSystemTrayIcon.ActivationReason.Trigger:
        global disabled, proc
        if disabled:
            proc = subprocess.Popen(['/usr/bin/python', rotate_py])
            tray.setIcon(QIcon(enabled_png))
        else:
            proc.kill();
            tray.setIcon(QIcon(disabled_png))
        disabled = not disabled


if __name__ == '__main__':
    disabled = True
    package = resources.files('autorotate')
    enabled_png = str(package.joinpath('icons/enabled.png'))
    disabled_png = str(package.joinpath('icons/disabled.png'))
    rotate_py = str(package.joinpath('rotate.py'))

    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)

    tray = QSystemTrayIcon()
    tray.setIcon(QIcon(disabled_png))
    tray.setVisible(True)
    tray.activated.connect(icon_activated)

    menu = QMenu()
    leave = QAction('Quit')
    leave.triggered.connect(app.quit)
    menu.addAction(leave)

    tray.setContextMenu(menu)
    app.exec_()
