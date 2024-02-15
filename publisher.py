"""Publisher class."""


class Publisher:
    """Publisher class."""

    topic_name = ''
    dds_latency = 0

    def __init__(self, topic_name, dds_latency):
        """Initialize publisher."""
        self.topic_name = topic_name
        self.dds_latency = dds_latency

    def print_info(self):
        """Print publisher info."""
        print('Publisher topic name: ' + self.topic_name)
        print('Publisher dds latency: ' + str(self.dds_latency))
