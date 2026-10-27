# Fig. 4: umbi writes the example MDP to mdp.umb, and PRISM writes the contents of mdp.umb in textual form:
#   prism -ex -importmodel mdp.umb -exportmodel mdp.umbt:format=umb,text
#   python run.py
import os
import subprocess

import umbi


def write_mdp(path):
    """The example MDP of the paper (Figs. 2-4), the same model as in the getting-started notebook,
    with the label "g", the reward "r", and the variables x and b of example.prism."""
    ats = umbi.ats.SimpleAts()
    ats.new_states(4)
    ats.initial_states = [0]
    ats.new_players(1)

    ats.new_choice(state=0, action_name="a", targets=[1, 2], probs=[0.5, 0.5])
    ats.new_choice(state=0, action_name="b", targets=[2, 3], probs=[0.2, 0.8])
    ats.new_choice(state=1, action_name="a", targets=[0, 1], probs=[0.9, 0.1])
    ats.new_choice_absorbing(state=2, action_name="tau")
    ats.new_choice_absorbing(state=3, action_name="tau")

    ats.new_ap_annotation("g").state_values = [False, False, False, True]
    ats.new_reward_annotation("r").choice_values = [0.0, 1.0, 0.0, 0.0, 0.0]

    valuations = ats.add_variable_valuations().add_state_valuations()
    x, b = valuations.new_variable("x"), valuations.new_variable("b")
    for state, (x_value, b_value) in enumerate([(0, False), (1, False), (2, False), (2, True)]):
        valuations.set_entity_valuation(state, {x: x_value, b: b_value})

    umbi.ats.write(ats, path)


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    write_mdp("mdp.umb")
    # The "text" export option makes PRISM write the contents of the UMB archive in textual form.
    # We need the explicit engine (-ex): the default engine adds an empty string as action 0.
    cmd = ["prism", "-ex", "-importmodel", "mdp.umb", "-exportmodel", "mdp.umbt:format=umb,text"]
    print("$ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)
    print("$ cat mdp.umbt")
    print(open("mdp.umbt").read())


if __name__ == "__main__":
    main()
