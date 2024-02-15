"""Timer class."""

from callback import Callback


class Timer:
    """Timer class."""

    phase = 0
    period = 0

    callback = 0

    def __init__(self, phase, period):
        """Initialize timer."""
        self.phase = phase
        self.period = period
        self.callback = 0

    def add_callback(self, node, callback_description):
        """Add callback to timer."""
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
        """Print timer info."""
        print('Timer phase: ' + str(self.phase))
        print('Timer period: ' + str(self.period))
        if self.callback != 0:
            self.callback.print_info()