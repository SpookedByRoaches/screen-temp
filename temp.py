import subprocess

devices = subprocess.check_output("pactl list sinks | awk '/Name|Description/ {print $0}'", shell=True).decode("utf8")

dev_list = devices.split("\n")
dev_names = []
dev_descs = []

for i in range(0, len(dev_list), 2):
	dev_names.append(dev_list[i])
	dev_descs.append(dev_list[i+1])

ret_code, choice = dialog.list_menu(dev_descs)

if ret_code == 0:
	subprocess.Popen(["notify-send", choice])
