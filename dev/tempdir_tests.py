import tempfile
import os

print(os.path.sep)

exit()

path = tempfile.mkdtemp()

print(path)

path = tempfile.mkdtemp('testing')

print(path)

path = tempfile.mkdtemp(f'{os.path.sep}testing')

print(path)
