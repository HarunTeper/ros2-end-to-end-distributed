"""Executor class."""

from subscription import Subscription
from timer import Timer


class Executor:
    """Executor class."""

    nodes = []
    dds_mode = 'synchronous'
    task_policy = 'timers_first'

    def __init__(self):
        """Initialize."""
        self.nodes = []
        self.dds_mode = 'synchronous'
        self.task_policy = 'timers_first'

    def get_node_index_from_task(self, task):
        """Get node index from task."""
        for index, node in enumerate(self.nodes):
            if task in node.timer_list or task in node.subscription_list:
                return index
        return -1

    def get_task_priority_comparison(self, task1, task2):
        """Get priority comparison."""
        task1_node_index = self.get_node_index_from_task(task1)
        task2_node_index = self.get_node_index_from_task(task2)
        if self.task_policy == 'timers_first':
            if isinstance(task1, Timer) and isinstance(task2, Subscription):
                return 1
            elif isinstance(task1, Subscription) and isinstance(task2, Timer):
                return 0
            elif isinstance(task1, Timer) and isinstance(task2, Timer):
                if task1_node_index < task2_node_index:
                    return 1
                elif task1_node_index > task2_node_index:
                    return 0
                else:
                    timer1_index = self.nodes[task1_node_index].timer_list.index(task1)
                    timer2_index = self.nodes[task2_node_index].timer_list.index(task2)
                    if timer1_index < timer2_index:
                        return 1
                    else:
                        return 0
            elif isinstance(task1, Subscription) and isinstance(task2, Subscription):
                if task1_node_index < task2_node_index:
                    return 1
                elif task1_node_index > task2_node_index:
                    return 0
                else:
                    subscription1_index = self.nodes[task1_node_index].subscription_list.index(task1)
                    subscription2_index = self.nodes[task2_node_index].subscription_list.index(task2)
                    if subscription1_index < subscription2_index:
                        return 1
                    else:
                        return 0
        elif self.task_policy == 'subscriptions_first':
            if isinstance(task1, Timer) and isinstance(task2, Subscription):
                return 0
            elif isinstance(task1, Subscription) and isinstance(task2, Timer):
                return 1
            elif isinstance(task1, Timer) and isinstance(task2, Timer):
                if task1_node_index < task2_node_index:
                    return 1
                elif task1_node_index > task2_node_index:
                    return 0
                else:
                    timer1_index = self.nodes[task1_node_index].timer_list.index(task1)
                    timer2_index = self.nodes[task2_node_index].timer_list.index(task2)
                    if timer1_index < timer2_index:
                        return 1
                    else:
                        return 0
            elif isinstance(task1, Subscription) and isinstance(task2, Subscription):
                if task1_node_index < task2_node_index:
                    return 1
                elif task1_node_index > task2_node_index:
                    return 0
                else:
                    subscription1_index = self.nodes[task1_node_index].subscription_list.index(task1)
                    subscription2_index = self.nodes[task2_node_index].subscription_list.index(task2)
                    if subscription1_index < subscription2_index:
                        return 1
                    else:
                        return 0
        else:
            if isinstance(task1, Timer) and isinstance(task2, Timer):
                if task1_node_index < task2_node_index:
                    return 1
                elif task1_node_index > task2_node_index:
                    return 0
                else:
                    timer1_index = self.nodes[task1_node_index].timer_list.index(task1)
                    timer2_index = self.nodes[task2_node_index].timer_list.index(task2)
                    if timer1_index < timer2_index:
                        return 1
                    else:
                        return 0
            elif isinstance(task1, Subscription) and isinstance(task2, Subscription):
                if task1_node_index < task2_node_index:
                    return 1
                elif task1_node_index > task2_node_index:
                    return 0
                else:
                    subscription1_index = self.nodes[task1_node_index].subscription_list.index(task1)
                    subscription2_index = self.nodes[task2_node_index].subscription_list.index(task2)
                    if subscription1_index < subscription2_index:
                        return 1
                    else:
                        return 0

    def add_node(self, node):
        """Add node to executor."""
        self.nodes.append(node)

    def set_dds_mode(self, mode):
        """Set DDS mode."""
        self.dds_mode = mode

    def set_task_policy(self, policy):
        """Set task policy."""
        self.task_policy = policy

    def print_info(self):
        """Print executor info."""
        print('Executor nodes: ' + str(len(self.nodes)))
        print('Executor DDS mode: ' + self.dds_mode)