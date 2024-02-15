"""Node class."""

from timer import Timer
from buffer import Buffer
from subscription import Subscription


class Node:
    """Node class."""

    name = ''

    subscription_list = []
    timer_list = []

    intra_node_communication_buffers = []

    def __init__(self, name):
        """Initialize node."""
        self.name = name
        self.subscription_list = []
        self.timer_list = []
        self.intra_node_communication_buffers = []

    def add_subscription(self, subscription_description):
        """Add subscription to node."""
        subscription = Subscription(subscription_description['topic_name'], subscription_description['buffer_size'])
        if 'callback' in subscription_description:
            subscription.add_callback(self, subscription_description['callback'])

        self.subscription_list.append(subscription)

    def add_timer(self, timer_description):
        """Add timer to node."""
        timer = Timer(timer_description['phase'], timer_description['period'])
        if 'callback' in timer_description:
            timer.add_callback(self, timer_description['callback'])

        self.timer_list.append(timer)

    def add_intra_node_communication_buffer(self, intra_node_communication_buffer_description):
        """Add intra node communication buffer to node."""
        # check if buffer with buffer_name is already in list
        for buffer in self.intra_node_communication_buffers:
            if buffer.name == intra_node_communication_buffer_description['buffer_name']:
                # buffer with buffer_name is already in list
                # overwrite write_latency if it is defined
                if 'write_latency' in intra_node_communication_buffer_description:
                    buffer.set_write_latency(intra_node_communication_buffer_description['write_latency'])
                return buffer
        if 'write_latency' not in intra_node_communication_buffer_description:
            self.intra_node_communication_buffers.append(Buffer(intra_node_communication_buffer_description['buffer_name'], buffer_size=float('inf')))
        else:
            self.intra_node_communication_buffers.append(Buffer(intra_node_communication_buffer_description['buffer_name'], buffer_size=float('inf'), write_latency=intra_node_communication_buffer_description['write_latency']))
        return self.intra_node_communication_buffers[-1]

    def print_info(self):
        """Print node info."""
        print('Node: ' + self.name)
        print('Number of timers: ' + str(len(self.timer_list)))
        print('Number of subscriptions: ' + str(len(self.subscription_list)))
        print('Number of intra node communication buffers: ' + str(len(self.intra_node_communication_buffers)))
        for timer in self.timer_list:
            timer.print_info()
        for subscription in self.subscription_list:
            subscription.print_info()
        for buffer in self.intra_node_communication_buffers:
            buffer.print_info()
