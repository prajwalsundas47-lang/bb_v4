_listeners = []

def register(cb):
    _listeners.append(cb)

def notify(msg):
    for cb in list(_listeners):
        try:
            cb(msg)
        except Exception:
            pass

def _on_bb_notify(msg):
    self.add_message("BB", msg)   # or however you append to chat_log

bb_notify.register(_on_bb_notify)
