import threading
import time
from signal import SIGINT
import subprocess
import unittest


class Main(unittest.TestCase):
    lines = []

    def test_zoozl(self):
        args = []
        args.append("/home/juris/py-programs/zoozl/bin/python")
        args.append("-u")
        args.append("/home/juris/py-programs/zoozl/source/zoozl.py")
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.get_stream(proc)
        found = False
        for i in self.lines:
            line = i.split()
            if "odoo.modules.registry:" in line[5] \
                    and "Registry" in line[6]:
                found = True
        msg = f"Last line should contain {line[5]}"
        self.assertTrue(found, msg=msg)
        proc.send_signal(SIGINT)
        proc.wait(timeout=4)

    def get_stream(self, proc):
        t = threading.Thread(target=self.read_items_from_proc, args=(proc,), daemon=True)
        t.start()
        a = t.is_alive()
        while a:
            t.join(timeout=7)
            a = t.is_alive()
            if a:
                break

    def read_items_from_proc(self, proc):
        a = True
        while a:
            self.lines.append(proc.stderr.readline().decode())
