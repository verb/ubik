
import shlex
import subprocess

# Fabric 1.0 changed changed the scope of cd() to only affect remote calls.
# With fabric >1.0 cd() was replaced with lcd() for local calls.  This helper
# function will execute commands independent of fabric and maintain <1.0 compat
def _local(command_string, cwd=None):
    print "[localhost] run:", command_string
    subprocess.check_call(shlex.split(command_string), cwd=cwd)

