# Testing framework

This is mostly here so I can remember what I did!

- I found this a hard repository to write tests for because it mostly interacts with a third party program very slowly
- THerefore, the testing procedures basically bypass this step, you can read how in the development example.
- This means we don't have perfect test coverage, but better than none.
- To run the tests, just run pytest from the command line
- To assess coverage of tests ```coverage run -m pytest``` then ```coverage report```
- Documentation coverage is included in the unit tests, but if you want to see detailed results (which you will if the unit tests fail) run ```interrogate ../TopasOpt -vv```
- these tests are setup to run automaticaly when you do ```git push```. This is done using the script at .git/hooks/pre-push
- note that this script is executed at the root of this repository, this took me a while to figure out

