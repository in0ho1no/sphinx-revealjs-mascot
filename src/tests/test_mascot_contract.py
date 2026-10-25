"""Python・JavaScript・CSS で、アクションと画像状態の名前が一致することを確認する。"""

import re
from pathlib import Path

from sphinx_revealjs_mascot.config import ACTIONS, DEFAULT_ACTIONS, STATES

_STATIC = Path(__file__).resolve().parents[1] / 'sphinx_revealjs_mascot/static/sphinx-revealjs-mascot'
_SCRIPT = (_STATIC / 'mascot.js').read_text(encoding='utf-8')
_STYLE = (_STATIC / 'mascot.css').read_text(encoding='utf-8')


def test_default_actions_can_be_specified_explicitly() -> None:
    explicit = {name for name, action in ACTIONS.items() if action.explicit}

    assert set(DEFAULT_ACTIONS.values()) <= explicit


def test_every_action_uses_a_known_image_and_non_negative_duration() -> None:
    for name, action in ACTIONS.items():
        assert action.image in STATES, name
        assert action.duration >= 0, name


def test_css_animates_exactly_the_actions_with_motion() -> None:
    styled = set(re.findall(r'\[data-state="([^"]+)"\]', _STYLE))

    assert styled == {name for name, action in ACTIONS.items() if action.motion}


def test_names_written_in_javascript_are_defined_in_python() -> None:
    actions = set(re.findall(r'(?:runAction\(|state\s*(?:===|!==|=)\s*|action\s*===\s*)"([a-z]+)"', _SCRIPT))
    sprites = set(re.findall(r'sprites\.([a-z]+)', _SCRIPT))
    defaults = set(re.findall(r'defaultActions\.([a-z]+)', _SCRIPT))

    assert {'idle', 'doze', 'wake'} <= actions <= set(ACTIONS)
    assert {'normal', 'blink'} <= sprites <= set(STATES)
    assert defaults == set(DEFAULT_ACTIONS)
