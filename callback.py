"""Callback class."""

from publisher import Publisher


class Callback:
    """Callback class."""

    wcet = 0
    publishers = []

    read_buffers = []
    write_buffers = []

    def __init__(self, wcet):
        """Initialize callback."""
        self.wcet = wcet
        self.publishers = []
        self.read_buffers = []
        self.write_buffers = []

    def add_publisher(self, publisher_topic_description):
        """Add publisher topic to callback."""
        self.publishers.append(Publisher(publisher_topic_description['topic_name'], publisher_topic_description['dds_latency']))

    def add_write_buffer(self, node, write_buffer_description):
        """Add write buffer to callback."""
        buffer = node.add_intra_node_communication_buffer(write_buffer_description)
        self.write_buffers.append(buffer)

    def add_read_buffer(self, node, read_buffer_description):
        """Add read buffer to callback."""
        buffer = node.add_intra_node_communication_buffer(read_buffer_description)
        self.read_buffers.append(buffer)

    def print_info(self):
        """Print callback info."""
        print('Callback wcet: ' + str(self.wcet))
        print('Number of publisher topics: ' + str(len(self.publishers)))
        print('Number of read buffers: ' + str(len(self.read_buffers)))
        print('Number of write buffers: ' + str(len(self.write_buffers)))
        for publisher_topic in self.publishers:
            publisher_topic.print_info()
        for read_buffer in self.read_buffers:
            read_buffer.print_info()
        for write_buffer in self.write_buffers:
            write_buffer.print_info()
