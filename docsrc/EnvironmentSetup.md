# Environment set up

These instructions demonstrate how to set up a new environment on ubuntu from scratch. It is assumed you already have python3.8 or greater installed.
These were tested on Ubunutu 18.04 but something very similar should work on most linux versions.

```bash
# optional: start a new screen session. This allows you to easily come back to this session later
# see here: https://linuxize.com/post/how-to-use-linux-screen/
screen -S TopasOpt

# check python version:
python3 -V
# should be >= 3.8 - update if you need to:
sudo apt install python3.8
# the above command will by default install python to the symbolic link python3.8
# you can google how to change this if you want to!

# make virtual environment:
python3.8 -m venv TopasOpt
# activate it:
source TopasOpt/bin/activate

# Make sure the version of your pip and setuptools is sufficient for manylinux2014 wheels.
# thank to this answer:
# https://stackoverflow.com/questions/64095094/command-python-setup-py-egg-info-failed-with-error-code-1-in-tmp
pip3 install -U pip
pip3 install -U setuptools

# install TopasOpt
pip install TopasOpt
# test installation:
python3  # enter a python session
import TopasOpt
Topas.__version__  # just to check it's there - should print e.g. 0.0.2
exit()  # exit python session.
```

you should now be able to set up and run the examples.

a few tips:

```bash
# to deactivate the virtual environment
deactivate
# to leave the screen session
hold ctrl, press a, release, then press d
# to reneter the screen session
screen -r TopasOpt  # or whatever name you gave this session
# to exit and terminate screen session
exit # if you are not inside the screen session when you type this you will kill your main sesson instead!
```
