"""スライド設定と、内容をまとめて表示する fragment を定義する。"""

from collections.abc import Callable
from typing import NoReturn

from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.application import Sphinx
from sphinx.errors import ExtensionError
from sphinx.util.docutils import SphinxDirective
from sphinx.writers.html5 import HTML5Translator
from sphinx_revealjs.nodes import revealjs_section

from sphinx_revealjs_mascot.config import parse_position

_EXPLICIT_ACTIONS = ('idle', 'jump', 'wink', 'surprise')


def _action(value: str) -> str:
    """明示指定できるアクションだけを受け付ける。"""
    if value not in _EXPLICIT_ACTIONS:
        raise ExtensionError(f'明示指定できないアクションです: {value!r}。指定可能: {_EXPLICIT_ACTIONS}')
    return value


def _position(value: str) -> str:
    """表示位置を検証し、ディレクティブの入力値を返す。"""
    parse_position(value)
    return value


class _StrictOptions(dict[str, Callable[[str], object]]):
    """不明なオプションを警告ではなくビルドエラーにする。"""

    def __missing__(self, key: str) -> NoReturn:
        raise ExtensionError(f'不明な mascot ディレクティブオプションです: {key}')


class MascotSettings(nodes.Invisible, nodes.Element):
    """スライドへ適用するまで設定を保持する非表示ノード。"""


class MascotFragment(nodes.General, nodes.Element):
    """囲まれた内容全体を1つの fragment として扱うノード。"""


class MascotDirective(Directive):
    """見出し直後のスライド設定を読み取る。"""

    option_spec = _StrictOptions(action=_action, position=_position)

    def run(self) -> list[nodes.Node]:
        """設定を表示しないノードとして返す。"""
        node = MascotSettings()
        node.attributes.update(self.options)
        node.source, node.line = self.state_machine.get_source_and_line(self.lineno)
        return [node]


class MascotFragmentDirective(SphinxDirective):
    """複数の段落やリストを1つの fragment にまとめる。"""

    has_content = True
    option_spec = _StrictOptions(action=_action)

    def run(self) -> list[nodes.Node]:
        """本文を解釈して fragment ノードへ格納する。"""
        self.assert_has_content()
        node = MascotFragment(classes=['fragment'])
        if 'action' in self.options:
            node['data-mascot-action'] = self.options['action']
        self.set_source_info(node)
        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]


def apply_slide_settings(app: Sphinx, doctree: nodes.document, docname: str) -> None:
    """設定を対応するスライドの section 属性へ統合する。"""
    seen: set[int] = set()
    for marker in list(doctree.findall(MascotSettings)):
        section = marker.parent
        if not isinstance(section, nodes.section):
            raise ExtensionError(f'{docname}:{marker.line}: mascot はスライドの見出し直後に置いてください')
        if id(section) in seen:
            raise ExtensionError(f'{docname}:{marker.line}: 同じスライドに mascot を複数指定できません')
        seen.add(id(section))
        attributes = next((child for child in section.children if isinstance(child, revealjs_section)), None)
        if attributes is None:
            attributes = revealjs_section()
            section.append(attributes)
        if 'action' in marker:
            attributes['data-mascot-action'] = marker['action']
        if 'position' in marker:
            position = parse_position(marker['position'])
            attributes['data-mascot-position'] = position.anchor
            attributes['data-mascot-x'] = f'{position.x:g}'
            attributes['data-mascot-y'] = f'{position.y:g}'
            attributes['data-mascot-facing'] = str(position.facing)
        section.remove(marker)


def visit_fragment(translator: HTML5Translator, node: MascotFragment) -> None:
    """まとまり全体を1つの HTML 要素で囲む。"""
    attributes = {'data-mascot-action': node['data-mascot-action']} if 'data-mascot-action' in node else {}
    translator.body.append(translator.starttag(node, 'div', **attributes))


def depart_fragment(translator: HTML5Translator, node: MascotFragment) -> None:
    """Fragment のまとまりを閉じる。"""
    translator.body.append('</div>\n')
