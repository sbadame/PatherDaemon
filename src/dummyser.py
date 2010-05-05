


class DummySerial:

    def write(msg):
        print("Message Received: %s" % msg)

    def flush():
        pass

    def readline():
        pass
