"""Base effects per action type. Pure: takes ActionInput + GameState, returns ActionEffects.

Numbers in this module are starting estimates — tune in playtesting.
"""

from src.engine.types import ActionEffects, ActionInput, ActionType, GameState


def calculate_base_effects(action: ActionInput, _state: GameState) -> ActionEffects:
    effects = ActionEffects()
    tokens = action.tokens
    actor = action.player_id

    match action.action_type:
        case ActionType.MILITARY_OFFENSIVE:
            if action.target_id is not None and tokens.MIL > 0:
                effects.add_resource_change(action.target_id, "MIL", -(tokens.MIL * 2))
            effects.tension_delta += min(tokens.MIL * 3, 12)

        case ActionType.MILITARY_DEFENSIVE:
            # Defense buffs are absorbed during interaction phase; here it only
            # adds the standard defensive tension bump.
            effects.tension_delta += 2

        case ActionType.DIPLOMATIC_PROPOSAL:
            effects.tension_delta -= min(tokens.DIP * 2, 8)

        case ActionType.DIPLOMATIC_MEDIATION:
            effects.tension_delta -= 8
            # The mediator earns reputation (DIP) from a successful mediation.
            # If mediation fails, the interaction phase will clear this and bump tension.
            effects.add_resource_change(actor, "DIP", 1)

        case ActionType.ECONOMIC_SANCTION:
            if action.target_id is not None and tokens.ECO > 0:
                effects.add_resource_change(action.target_id, "ECO", -int(tokens.ECO * 1.5))
            effects.tension_delta += 3

        case ActionType.ECONOMIC_AID:
            if action.target_id is not None and tokens.ECO > 0:
                effects.add_resource_change(action.target_id, "ECO", tokens.ECO)
            effects.tension_delta -= 2

        case ActionType.INTEL_ESPIONAGE | ActionType.INTEL_COUNTER:
            # Pure intel actions don't change resources by themselves in Phase 2.
            # Their effect is informational (Phase 3) or shows up in interactions.
            pass

        case ActionType.INFO_EXPOSE:
            effects.tension_delta += 5
            if action.target_id is not None:
                effects.add_resource_change(action.target_id, "DIP", -2)

        case ActionType.PACT_BREAK:
            effects.tension_delta += 7
            effects.add_resource_change(actor, "DIP", -1)

        case ActionType.GENERIC:
            # Tokens with no specific intent — minimal effect, follows posture only.
            pass

    # Posture adjusts tension regardless of action_type.
    match action.posture:
        case "confrontational":
            effects.tension_delta += 2
        case "cooperative":
            effects.tension_delta -= 1
        case "ambiguous":
            effects.tension_delta += 1

    return effects
