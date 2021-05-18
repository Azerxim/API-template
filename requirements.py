import subprocess
import sys


def install(package, version = None):
    if version == None:
        pv = package
    else:
        pv = "{p}=={v}".format(p=package, v=version)
    subprocess.call([sys.executable, "-m", "pip", "install", "-U", pv])


# Base
install("pip")

# API
install("fastapi[all]", "0.63.0")

# Base de données
install("SQLAlchemy", "1.4.3")
