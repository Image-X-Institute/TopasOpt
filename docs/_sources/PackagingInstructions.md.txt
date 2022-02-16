# Packaging instructions

nb: this is mostly for me so I can remember how I did this :-P

Packaging for this project has been setup based on [this tutorial](https://packaging.python.org/en/latest/tutorials/packaging-projects/).
To update the distribution code, use the following commands.
Required depencies are defined in setup.cfg

```bash
# first update version number in TopasOpt.__init__

# delete any existing distribution files
rm -r dist
# build distribution packages
python -m build
# upload built package
python3 -m twine upload --repository testpypi dist/*  # if testing
twine upload dist/*  # for real
```