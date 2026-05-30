import difflib

class DiffService:
    def compare(self, text1: str, text2: str) -> list:
        d = difflib.Differ()
        diff = list(d.compare(text1.splitlines(), text2.splitlines()))
        return [{"type": line[0], "text": line[2:]} for line in diff]
