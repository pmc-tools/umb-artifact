#!/usr/bin/env python3
"""Reorder the states of a UMB file so that the initial states come first.

With n initial states, the result has them at indices 0..n-1 (in their original
relative order), followed by all other states (also in their original relative
order). Since choices and branches are laid out contiguously per state (CSR),
they are reordered accordingly, branch targets are remapped, and all per-state,
per-choice and per-branch data (exit rates, Markovian flags, players, actions,
annotations, valuations, observations) is permuted along with them.
"""

import argparse
import logging
import sys

import umbi
from umbi.umb import ExplicitUmb

logger = logging.getLogger("umb_reorder")


def _permute(values: list | None, new_to_old: list[int]) -> list | None:
	"""Return the list whose i-th element is values[new_to_old[i]]."""
	if values is None:
		return None
	assert len(values) == len(new_to_old), f"expected {len(new_to_old)} entries, got {len(values)}"
	return [values[o] for o in new_to_old]


def _permute_ranges(csr: list[int] | None, new_to_old: list[int]) -> tuple[list[int] | None, list[int]]:
	"""Reorder a CSR mapping according to a permutation of its sources.

	:param csr: the CSR mapping (n+1 entries), or None for the default identity mapping
	:param new_to_old: permutation of the n sources
	:return: the new CSR mapping (None if the input was None), and the induced
		new-to-old permutation of the targets
	"""
	if csr is None:
		return None, list(new_to_old)
	assert len(csr) == len(new_to_old) + 1, f"CSR mapping has {len(csr)} entries, expected {len(new_to_old) + 1}"
	new_csr = [0]
	targets_new_to_old = []
	for o in new_to_old:
		lo, hi = csr[o], csr[o + 1]
		targets_new_to_old.extend(range(lo, hi))
		new_csr.append(new_csr[-1] + (hi - lo))
	return new_csr, targets_new_to_old


def initial_first_order(umb: ExplicitUmb) -> list[int]:
	"""Return the new-to-old state permutation that puts initial states first (stable)."""
	initial = [s for s, b in enumerate(umb.state_is_initial) if b]
	other = [s for s, b in enumerate(umb.state_is_initial) if not b]
	return initial + other


def reorder_states(umb: ExplicitUmb, state_new_to_old: list[int]) -> ExplicitUmb:
	"""Return a copy of umb with its states reordered.

	:param umb: the input model (not modified)
	:param state_new_to_old: permutation of the states; new state i is old state state_new_to_old[i]
	"""
	ts = umb.index.transition_system
	num_states = ts.num_states

	# validate the state permutation and invert it (needed to remap branch targets)
	if sorted(state_new_to_old) != list(range(num_states)):
		raise ValueError("not a permutation of the states")
	state_old_to_new = [0] * num_states
	for n, o in enumerate(state_new_to_old):
		state_old_to_new[o] = n

	# derive the choice and branch permutations: choices follow their states, branches their choices,
	# each keeping their original order within their state/choice; also rebuild the CSR mappings
	state_to_choices, choice_new_to_old = _permute_ranges(umb.state_to_choices, state_new_to_old)
	choice_to_branches, branch_new_to_old = _permute_ranges(umb.choice_to_branches, choice_new_to_old)
	if len(choice_new_to_old) != ts.num_choices:
		raise ValueError(f"model has {len(choice_new_to_old)} choices, but index says {ts.num_choices}")
	if len(branch_new_to_old) != ts.num_branches:
		raise ValueError(f"model has {len(branch_new_to_old)} branches, but index says {ts.num_branches}")
	new_to_old = {"states": state_new_to_old, "choices": choice_new_to_old, "branches": branch_new_to_old}

	# helper for data whose entity kind is only known at runtime (annotations, valuations, observations)
	def permute_entity(entity: str, values: list | None) -> list | None:
		# observations and players are not reordered
		return _permute(values, new_to_old[entity]) if entity in new_to_old else values

	# branch targets: permute the branches, and also map each target to its new state index;
	# absent file means every branch targets state 0 (TO1 default)
	branch_to_target = umb.branch_to_target
	if branch_to_target is None and ts.num_branches > 0:
		branch_to_target = [0] * ts.num_branches
	if branch_to_target is not None:
		branch_to_target = [state_old_to_new[t] for t in _permute(branch_to_target, branch_new_to_old)]

	# annotations (rewards, aps, custom groups): group -> name -> entity kind -> values
	annotations = None
	if umb.annotations is not None:
		annotations = {
			group: {
				name: {entity: permute_entity(entity, values) for entity, values in per_entity.items()}
				for name, per_entity in per_name.items()
			}
			for group, per_name in umb.annotations.items()
		}

	# valuations: entity kind -> values
	valuations = None
	if umb.valuations is not None:
		valuations = {entity: permute_entity(entity, values) for entity, values in umb.valuations.items()}

	# observations: apply to either states or branches
	entity_to_observation = umb.entity_to_observation
	if entity_to_observation is not None:
		entity_to_observation = permute_entity(ts.observations_apply_to, entity_to_observation)

	# assemble the result; data indexed by states/choices/branches with a fixed entity kind is permuted
	# right here, so new such fields go in the matching group below (and the index stays unchanged,
	# since all counts remain the same)
	return ExplicitUmb(
		index=umb.index,
		# per-state data
		state_is_initial=_permute(umb.state_is_initial, state_new_to_old),
		state_to_choices=state_to_choices,
		state_to_player=_permute(umb.state_to_player, state_new_to_old),
		state_is_markovian=_permute(umb.state_is_markovian, state_new_to_old),
		state_to_exit_rate=_permute(umb.state_to_exit_rate, state_new_to_old),
		# per-choice data
		choice_to_branches=choice_to_branches,
		choice_to_choice_action=_permute(umb.choice_to_choice_action, choice_new_to_old),
		# per-branch data
		branch_to_target=branch_to_target,
		branch_to_probability=_permute(umb.branch_to_probability, branch_new_to_old),
		branch_to_branch_action=_permute(umb.branch_to_branch_action, branch_new_to_old),
		# indexed by action, not by state/choice/branch: unchanged
		choice_action_to_string=umb.choice_action_to_string,
		branch_action_to_string=umb.branch_action_to_string,
		# data with entity kinds given at runtime, permuted above
		annotations=annotations,
		valuations=valuations,
		entity_to_observation=entity_to_observation,
	)


def main(argv: list[str] | None = None) -> int:
	# command line
	parser = argparse.ArgumentParser(
		description="Reorder the states of a UMB file so that the n initial states occupy indices 0..n-1."
	)
	parser.add_argument("input", help="input UMB file")
	parser.add_argument("output", help="output UMB file")
	parser.add_argument("-v", "--verbose", action="store_true", help="show umbi's log messages")
	args = parser.parse_args(argv)

	logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s: %(message)s")

	# read; strict: fail on files umbi does not know, rather than silently dropping them
	umb = umbi.umb.read(args.input, strict=True)

	# reorder (always, even if the initial states already come first, so the output is always written)
	order = initial_first_order(umb)
	num_initial = sum(umb.state_is_initial)
	old_initial = order[:num_initial]
	reordered = reorder_states(umb, order)

	# write; keep the original file-data (tool, version, ...) rather than replacing it with umbi's
	umbi.umb.write(reordered, args.output, insert_umbi_metadata=False)

	# report which states were moved
	shown = ", ".join(map(str, old_initial[:10])) + (", ..." if num_initial > 10 else "")
	print(f"{args.input} -> {args.output}: moved {num_initial} initial state(s) [{shown}] to indices 0..{num_initial - 1}")
	return 0


if __name__ == "__main__":
	sys.exit(main())
