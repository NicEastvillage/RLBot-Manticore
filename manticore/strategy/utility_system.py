class UtilitySystem:

    def __init__(self, states, last_choice_bias=0.1):
        self.options = states
        self.last_chosen_option = None
        self.last_choise_bias = last_choice_bias
        assert len(states) > 0, "Utility system has no options"

    def get_best_state(self, agent):

        best_option = self.options[0]
        best_option_score = 0
        for option in self.options:
            score = option.utility_score(agent)
            if option == self.last_chosen_option:
                score += self.last_choise_bias
            if score > best_option_score:
                best_option = option
                best_option_score = score
        if self.last_chosen_option != best_option:
            if self.last_chosen_option is not None:
                self.last_chosen_option.end(agent)
            best_option.begin(agent)

        self.last_chosen_option = best_option

        return best_option


class UtilityState:
    def utility_score(self, agent):
        raise NotImplementedError

    def run(self, agent):
        pass

    def begin(self, agent):
        pass

    def end(self, agent):
        pass
