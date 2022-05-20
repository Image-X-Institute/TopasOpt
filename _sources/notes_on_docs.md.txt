# notes on docs

These notes are mainly for me to remember how to update the docs :-P

requirements: sphinx recommonmark sphinx_rtd_theme sphinx_markdown_tables


From docsrc, ```make html``` produces a copy of the docs at docs/html.
```make github``` produces a copy at docs/github, which is the version hosted by github.

## including new examples

Each example contains a readme, which is also included in the docs.
For new examples, the following steps should be taken:

- all images go in docsrc/__resources
- update docsrc/conf.py with the new exmple (around line 30).
- These two steps ensure the new example readme is included in the docs and images formatted properly. 
