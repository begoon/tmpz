import contextlib
import io
import sys
import time

cmd = "ls -al"


class Tee(io.TextIOBase):
    def __init__(self):
        self._stdout = sys.stdout
        self._capture = []

    def write(self, data):
        self._stdout.write(data)
        self._stdout.flush()
        self._capture.append(data)

    def capture(self):
        return ''.join(self._capture)


tee = Tee()
with contextlib.redirect_stdout(tee):
    sys.stdout.write("...")
    time.sleep(3)
    print("os.system(cmd)")

print("captured")
print(tee.capture())
