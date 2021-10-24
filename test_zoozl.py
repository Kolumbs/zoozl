import threading
import time
from signal import SIGINT
import subprocess
import os
import unittest


class Main(unittest.TestCase):
    lines = []

    def test_zoozl(self):
        args = []
        os.chdir("../")
        args.append("bin/python")
        args.append("-u")
        args.append("source/zoozl.py")
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.get_stream(proc)
        found = False
        for i in self.lines:
            line = i.split()
            test = "odoo.modules.registry:"
            if test in line \
                    and "Registry" in line[6]:
                found = True
        proc.send_signal(SIGINT)
        proc.wait(timeout=4)
        proc.poll()
        msg = f"Last line should contain {test} in {line}"
        self.assertTrue(found, msg=msg)

    def get_stream(self, proc):
        t = threading.Thread(target=self.read_items_from_proc, args=(proc,), daemon=True)
        t.start()
        a = t.is_alive()
        while a:
            t.join(timeout=8)
            a = t.is_alive()
            if a:
                break

    def read_items_from_proc(self, proc):
        a = True
        while a:
            self.lines.append(proc.stderr.readline().decode())
