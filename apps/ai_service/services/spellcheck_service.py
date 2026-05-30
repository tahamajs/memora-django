from spellchecker import SpellChecker

class SpellCheckService:
    def __init__(self):
        self.spell = SpellChecker()

    def check(self, text: str) -> list:
        words = text.split()
        misspelled = self.spell.unknown(words)
        return [{"word": word, "suggestions": list(self.spell.candidates(word))} for word in misspelled]
