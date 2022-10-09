import subprocess
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon


disabled = True


def icon_activated(reason):
    if reason == QSystemTrayIcon.ActivationReason.Trigger:
        global disabled, proc
        if disabled:
            proc = subprocess.Popen(["/usr/bin/python", "rotate.py"])
            tray.setIcon(QIcon("icons/icon.png"))
        else:
            proc.kill();
            tray.setIcon(QIcon("icons/disabled.png"))
        disabled = not disabled


app = QApplication([])
app.setQuitOnLastWindowClosed(False)

tray = QSystemTrayIcon()
tray.setIcon(QIcon("icons/disabled.png"))
tray.setVisible(True)
tray.activated.connect(icon_activated)

menu = QMenu()
leave = QAction("Quit")
leave.triggered.connect(app.quit)
menu.addAction(leave)

tray.setContextMenu(menu)

app.exec_()
