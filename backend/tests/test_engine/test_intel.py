"""Phase D: the deterministic intel engine — who learns what after a turn."""

from src.engine.intel import compute_private_observations
from src.engine.resolver import resolve_turn
from src.engine.types import ActionType
from tests.test_engine._helpers import make_action, make_pact, make_player, make_state

HIDDEN = {"esparta": "Recuperar la hegemonía del Peloponeso sin enfrentarse a Macedonia."}


def _observations(viewer, actions, state, int_level, hidden=None):
    result = resolve_turn(actions, state)
    return compute_private_observations(
        viewer_id=viewer,
        resolved_actions=result.resolved_actions,
        state=state,
        int_level=int_level,
        hidden_objectives=hidden or HIDDEN,
    )


def test_successful_espionage_reveals_directive_and_secret_pact() -> None:
    state = make_state(
        make_player("atenas", INT=10),
        make_player("esparta"),
        make_player("corinto"),
        pacts=[make_pact("esparta", "corinto", "alliance", is_secret=True)],
    )
    actions = [
        make_action(
            "atenas", ActionType.INTEL_ESPIONAGE, target_id="esparta", intel=2
        ),
        make_action(
            "esparta",
            ActionType.GENERIC,
            directive="Reforzar la guarnición del istmo en silencio.",
            mil=3,
        ),
        make_action("corinto", ActionType.GENERIC),
    ]
    obs = _observations("atenas", actions, state, int_level=10)
    assert obs is not None
    assert "ESPIONAGE SUCCESS on esparta" in obs
    assert "Reforzar la guarnición" in obs
    assert "SECRET UNCOVERED" in obs and "covert alliance pact with corinto" in obs


def test_espionage_with_low_int_gets_directive_but_no_secret() -> None:
    state = make_state(
        make_player("atenas", INT=4),
        make_player("esparta"),
        pacts=[make_pact("esparta", "atenas", "trade", is_secret=True)],
    )
    actions = [
        make_action("atenas", ActionType.INTEL_ESPIONAGE, target_id="esparta", intel=1),
        make_action("esparta", ActionType.GENERIC, directive="Plan secreto."),
    ]
    obs = _observations("atenas", actions, state, int_level=4)
    assert "ESPIONAGE SUCCESS" in obs
    assert "SECRET UNCOVERED" not in obs


def test_espionage_without_secret_pact_hints_hidden_objective() -> None:
    state = make_state(make_player("atenas", INT=12), make_player("esparta"))
    actions = [
        make_action("atenas", ActionType.INTEL_ESPIONAGE, target_id="esparta", intel=2),
        make_action("esparta", ActionType.GENERIC, directive="x"),
    ]
    obs = _observations("atenas", actions, state, int_level=12)
    assert "hidden agenda" in obs
    assert "hegemonía del Peloponeso" in obs


def test_countered_espionage_burns_spy_and_warns_target() -> None:
    state = make_state(make_player("atenas"), make_player("esparta"))
    actions = [
        make_action("atenas", ActionType.INTEL_ESPIONAGE, target_id="esparta", intel=1),
        make_action("esparta", ActionType.INTEL_COUNTER, intel=3),
    ]
    result = resolve_turn(actions, state)
    spy_obs = compute_private_observations(
        viewer_id="atenas",
        resolved_actions=result.resolved_actions,
        state=state,
        int_level=15,
        hidden_objectives=HIDDEN,
    )
    assert "ESPIONAGE FAILED" in spy_obs
    assert "ESPIONAGE SUCCESS" not in spy_obs
    target_obs = compute_private_observations(
        viewer_id="esparta",
        resolved_actions=result.resolved_actions,
        state=state,
        int_level=5,
        hidden_objectives=HIDDEN,
    )
    # Even with low INT, catching a spy red-handed is a verified fact.
    assert "COUNTER-INTELLIGENCE" in target_obs
    assert "atenas" in target_obs


def test_intel_share_pact_shares_partner_picture() -> None:
    state = make_state(
        make_player("atenas"),
        make_player("tebas"),
        pacts=[make_pact("atenas", "tebas", "intel_share")],
    )
    actions = [
        make_action("atenas", ActionType.GENERIC),
        make_action(
            "tebas", ActionType.MILITARY_OFFENSIVE, target_id="atenas", mil=4,
            directive="Marchar sobre el Ática.",
        ),
    ]
    obs = _observations("atenas", actions, state, int_level=3)
    # Low INT, but the pact still delivers the partner's own picture.
    assert "SHARED BY tebas" in obs
    assert "main effort on MIL" in obs


def test_passive_signals_scale_with_int() -> None:
    state = make_state(make_player("atenas"), make_player("macedonia"), make_player("corinto"))
    actions = [
        make_action("atenas", ActionType.GENERIC),
        make_action(
            "macedonia", ActionType.MILITARY_OFFENSIVE, target_id="corinto", mil=4,
            directive="Tomar el paso de las Termópilas.",
        ),
        make_action("corinto", ActionType.GENERIC),
    ]
    high = _observations("atenas", actions, state, int_level=12)
    assert "NETWORK REPORT on macedonia" in high
    assert "Termópilas" in high

    fuzzy = _observations("atenas", actions, state, int_level=7)
    assert "NETWORK REPORT (partial) on macedonia" in fuzzy
    assert "Termópilas" not in fuzzy
    assert "main effort on MIL" in fuzzy

    low = _observations("atenas", actions, state, int_level=3)
    assert low is None
