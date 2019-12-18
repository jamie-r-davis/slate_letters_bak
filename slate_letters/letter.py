class Letter:

    def __init__(self, decision, letter, application, pdf, filename, **kwargs):
        self.decision = decision
        self.letter = letter
        self.application = application
        self.pdf = pdf
        self.filename = filename
        self.kwargs = kwargs

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.decision}>"

    def as_dict(self):
        return self.__dict__
