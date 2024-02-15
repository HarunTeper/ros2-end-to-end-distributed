"""Buffer class."""


class Buffer:
    """Buffer class."""

    name = ''
    write_latency = 0
    buffer_size = 0

    buffer_messages = []

    def __init__(self, name, buffer_size=0, write_latency=0):
        """Initialize buffer."""
        self.name = name
        self.buffer_size = buffer_size
        self.write_latency = write_latency
        self.buffer_messages = []

    def set_write_latency(self, write_latency):
        """Set write latency."""
        self.write_latency = write_latency

    def receive_message(self, message):
        """Receive message."""
        discarded_message = None
        if len(self.buffer_messages) >= self.buffer_size:
            discarded_message = self.buffer_messages.pop(0)
        self.buffer_messages.append(message)
        return discarded_message

    def print_info(self):
        """Print buffer info."""
        print('Buffer name: ' + self.name)
        print('Buffer size: ' + str(self.buffer_size))
        print('Buffer write latency: ' + str(self.write_latency))
        print('Buffer messages: ' + str(len(self.buffer_messages)))
