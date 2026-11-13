from orders.checkout import Order, place_order


class FakeStore:
    def __init__(self):
        self.saved = []

    def save(self, order):
        self.saved.append(order)


class FakeNotifications:
    def __init__(self):
        self.sent = []

    def send_confirmation(self, order_id, email):
        self.sent.append((order_id, email))


def test_place_order_saves_and_confirms():
    store, notifications = FakeStore(), FakeNotifications()
    place_order(Order("o-1", "ana@example.com", 1250), store, notifications)
    assert store.saved and notifications.sent == [("o-1", "ana@example.com")]
