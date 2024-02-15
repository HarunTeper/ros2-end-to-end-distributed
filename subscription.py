"""Subscription class."""

from buffer import Buffer

from callback import Callback


class Subscription:
    """Subscription class."""

    subscription_topic = ''

    callback = 0

    dds_buffer = 0

    def __init__(self, subscription_topic, buffer_size):
        """Initialize subscription."""
        self.subscription_topic = subscription_topic
        self.callback = 0
        self.dds_buffer = Buffer('dds_buffer_'+subscription_topic, buffer_size=buffer_size)

    def add_callback(self, node, callback_description):
        """Add callback to subscription."""
        self.callback = Callback(callback_description['wcet'])

        if 'dds_communication' in callback_description:
            if 'publishers' in callback_description['dds_communication']:
                for publisher_topic_description in callback_description['dds_communication']['publishers']:
                    self.callback.add_publisher(publisher_topic_description)

        if 'intra_node_communication' in callback_description:
            if 'write_buffers' in callback_description['intra_node_communication']:
                for intra_node_communication_description in callback_description['intra_node_communication']['write_buffers']:
                    self.callback.add_write_buffer(node, intra_node_communication_description)
            if 'read_buffers' in callback_description['intra_node_communication']:
                for intra_node_communication_description in callback_description['intra_node_communication']['read_buffers']:
                    self.callback.add_read_buffer(node, intra_node_communication_description)

    def print_info(self):
        """Print subscription info."""
        print('Subscription topic: ' + self.subscription_topic)
        self.dds_buffer.print_info()
        if self.callback != 0:
            self.callback.print_info()