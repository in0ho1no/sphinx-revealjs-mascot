"""Markdown とキャラクターを使うスライドの最小設定。"""

project = '発表タイトル'
extensions = ['myst_parser', 'sphinx_revealjs_mascot']
root_doc = 'index'
source_suffix = {'.md': 'markdown'}
language = 'ja'
exclude_patterns = ['_build']

revealjs_static_path = ['_static']
revealjs_css_files = ['slides.css']
revealjs_style_theme = 'white'
revealjs_script_conf = {
    'width': 1280,
    'height': 720,
    'margin': 0.06,
    'center': False,
    'transition': 'none',
    'hash': True,
}
revealjs_script_plugins = [
    {'name': 'RevealNotes', 'src': 'revealjs/plugin/notes/notes.js'},
]
