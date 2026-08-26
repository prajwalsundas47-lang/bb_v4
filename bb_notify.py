_listeners = []

def register(cb):
    _listeners.append(cb)

def notify(msg):
    for cb in list(_listeners):
        try:
            cb(msg)
        except Exception:
            pass


