class LastMessages:
    def __init__(self, max_length):
        self._max_length = max_length
        self.messages = {}

    def add(self, id, date, name, text):
        self.messages[id] = date, name, text
        self._maybe_drop_oldest()

    def edit(self, id, new_text):
        date, name, _ = self.messages[id]
        self.messages[id] = date, name, new_text
        self._maybe_drop_oldest()

    @property
    def total_length(self):
        return sum(len(m[2]) for m in self.messages.values())

    def _maybe_drop_oldest(self):
        while self.total_length > self._max_length:
            self.messages.pop(next(iter(self.messages)))

    def get_all(self):
        return list(self.messages.values())


def test_last_messages_add_two():
    db = LastMessages(100)
    db.add(1, "t1", "n1", "a")
    db.add(2, "t2", "n2", "b")

    assert db.get_all() == [('t1', 'n1', 'a'), ('t2', 'n2', 'b')]


def test_last_messages_add_three_removes_first():
    db = LastMessages(2)
    db.add(1, "t1", "n1", "a")
    db.add(2, "t2", "n2", "b")
    db.add(3, "t3", "n1", "c")

    assert db.get_all() == [('t2', 'n2', 'b'), ('t3', 'n1', 'c')]


def test_last_messages_edit():
    db = LastMessages(3)
    db.add(1, "t1", "n1", "a")
    db.add(2, "t2", "n2", "b")
    db.add(3, "t3", "n1", "c")

    db.edit(2, "e")

    assert db.get_all() == [('t1', 'n1', 'a'), ('t2', 'n2', 'e'), ('t3', 'n1', 'c')]


def test_long_edit_removes_first():
    db = LastMessages(3)
    db.add(1, "t1", "n1", "a")
    db.add(2, "t2", "n2", "b")
    db.add(3, "t3", "n1", "c")

    db.edit(2, "ee")

    assert db.get_all() == [('t2', 'n2', 'ee'), ('t3', 'n1', 'c')]
