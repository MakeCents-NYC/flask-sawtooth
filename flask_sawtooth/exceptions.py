class BalanceNotFound(ValueError):
    def __repr__(self):
        return "Failed to retrieve makecents balance."
