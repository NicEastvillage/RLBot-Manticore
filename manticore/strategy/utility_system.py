class UtilitySystem:

    def __init__(self, states, last_choice_bias=0.1):
        self.options = states
        self.last_chosen_option = None
        self.last_choise_bias = last_choice_bias
        assert len(states) > 0, "Utility system has no options"

    def get_best_state(self, agent):

        best_option = None
        best_option_score = 0
        for option in self.options:
            score = option.utility_score(agent)
            if option == self.last_chosen_option:
                score += self.last_choise_bias
            if score > best_option_score:
                best_option = option
                best_option_score = score

        return best_option
