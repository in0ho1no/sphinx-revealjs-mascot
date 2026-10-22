"""利用サンプルで共用する Sphinx 設定。仕様の正本は docs/SPEC.md。"""

project = 'sphinx-revealjs-mascot examples'
extensions = ['sphinx_revealjs', 'myst_parser', 'sphinx_revealjs_mascot']
root_doc = 'slides'
language = 'ja'
exclude_patterns = ['_build']
