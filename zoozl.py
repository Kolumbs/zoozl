import subprocess
import sys


if __name__ == "__main__":
    proc = subprocess.run(("../bin/python", "odoo/odoo-bin", "-dzoozl", "-rsanita", "-wblock", "-ubase"))
    proc.check_returncode()
    sys.exit()
