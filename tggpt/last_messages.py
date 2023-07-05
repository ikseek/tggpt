class LastMessages:
    def __init__(self, max_length):
        self._max_length = max_length
        self.messages = {}

    def add(self, id, text):
        self.messages[id] = text
        self._maybe_drop_oldest()

    def edit(self, id, new_text):
        self.messages[id] = new_text
        self._maybe_drop_oldest()

    @property
    def total_length(self):
        return sum(len(m) for m in self.messages.values())

    def _maybe_drop_oldest(self):
        while self.total_length > self._max_length:
            self.messages.pop(next(iter(self.messages)))

    def get_all(self):
        return list(self.messages.values())


def test_last_messages_add_two():
    db = LastMessages(100)
    db.add(1, "a")
    db.add(2, "b")

    assert db.get_all() == ["a", "b"]


def test_last_messages_add_three_removes_first():
    db = LastMessages(2)
    db.add(1, "a")
    db.add(2, "b")
    db.add(3, "c")

    assert db.get_all() == ["b", "c"]


def test_last_messages_edit():
    db = LastMessages(3)
    db.add(1, "a")
    db.add(2, "b")
    db.add(3, "c")

    db.edit(2, "e")

    assert db.get_all() == ["a", "e", "c"]


def test_long_edit_removes_first():
    db = LastMessages(3)
    db.add(1, "a")
    db.add(2, "b")
    db.add(3, "c")

    db.edit(2, "ee")

    assert db.get_all() == ["ee", "c"]
