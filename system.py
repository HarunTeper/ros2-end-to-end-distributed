"""System class."""


import yaml

from executor import Executor
from node import Node


class System:
    """System class."""

    nodes = []
    chains = []
    executors = []

    def __init__(self, file=None):
        """Initialize system."""
        self.nodes = []
        self.chains = []
        self.executors = []

        if file is not None:
            self.read_nodes_from_yaml(file)
            self.print_info()
            self.create_chains()

    def read_nodes_from_yaml(self, file):
        """Read nodes from YAML file."""
        print('----------------------------------------')
        print()
        print('System configuration: ' + file + '\n')
        with open(file, 'r', encoding='utf-8') as stream:
            data = yaml.safe_load(stream)

            for node in data['nodes']:
                # check if timers key exists
                print('Node: ' + node['name'])
                if 'timers' in node:
                    # print the number of timers
                    print('Number of timers: ' + str(len(node['timers'])))
                if 'subscriptions' in node:
                    # print the number of subscriptions
                    print('Number of subscriptions: ' + str(len(node['subscriptions'])))
                self.add_node(node)
            for executor in data['executors']:
                self.add_executor(executor)
            print()
        print('----------------------------------------')

    def add_node(self, node_description):
        """Add node to system."""
        node = Node(node_description['name'])

        # add timers to node
        if 'timers' in node_description:
            for timer_description in node_description['timers']:
                node.add_timer(timer_description)

        # add subscriptions to node
        if 'subscriptions' in node_description:
            for subscription_description in node_description['subscriptions']:
                node.add_subscription(subscription_description)

        self.nodes.append(node)

    def add_executor(self, executor_description):
        """Add executor to system."""
        self.executors.append(Executor())
        for node in executor_description['nodes']:
            print(node)
            for node_object in self.nodes:
                if node_object.name == node['name']:
                    self.executors[-1].add_node(node_object)
        self.executors[-1].set_dds_mode(executor_description['dds_mode'])
        self.executors[-1].set_task_policy(executor_description['task_policy'])

    def get_executor_by_task(self, task):
        """Get executor by task."""
        for executor in self.executors:
            for node in executor.nodes:
                for timer in node.timer_list:
                    if timer == task:
                        return executor
                for subscription in node.subscription_list:
                    if subscription == task:
                        return executor

    def create_chains(self):
        """Create chains."""
        starter_tasks = []
        chains = []
        # find the timers without an intra_node read buffer
        for node in self.nodes:
            for timer in node.timer_list:
                if len(timer.callback.read_buffers) == 0:
                    starter_tasks.append(timer)
        for starter_task in starter_tasks:
            chains.append([starter_task])
        extended_chains = self.extend_chains(chains)
        self.chains = extended_chains

        print('----------------------------------------')
        print()
        print('Number of chains: ' + str(len(self.chains)))
        for chain in self.chains:
            print('Chain length: ' + str(len(chain)))
        print()
        print('----------------------------------------')

    def extend_chains(self, chains):
        """Extend chain."""
        for _ in chains:
            chain = chains.pop(0)
            if len(chain[-1].callback.write_buffers) > 0 or len(chain[-1].callback.publishers) > 0:
                new_chains = []
                for node in self.nodes:
                    for subscription in node.subscription_list:
                        if subscription.subscription_topic in [publisher.topic_name for publisher in chain[-1].callback.publishers]:
                            new_chain = chain.copy()
                            new_chain.append(subscription)
                            new_chains.extend(self.extend_chains([new_chain]))
                        if any(buffer in chain[-1].callback.write_buffers for buffer in subscription.callback.read_buffers):
                            new_chain = chain.copy()
                            new_chain.append(subscription)
                            new_chains.extend(self.extend_chains([new_chain]))
                    for tmr in node.timer_list:
                        if any(buffer in chain[-1].callback.write_buffers for buffer in tmr.callback.read_buffers):
                            new_chain = chain.copy()
                            new_chain.append(tmr)
                            new_chains.extend(self.extend_chains([new_chain]))
                    # Add the new chains to the chains list
                chains.extend(new_chains)
            # If the element is an actuator, return the chain as a list for the extension
            else:
                chains.append(chain)
                return chains
        # Return all chains
        return chains

    def print_info(self):
        """Print system info."""
        print()
        print('System info:')
        print()
        print('Number of nodes: ' + str(len(self.nodes)))
        print('Number of executors: ' + str(len(self.executors)))
        print()
        for node in self.nodes:
            node.print_info()
        print()
        for executor in self.executors:
            executor.print_info()
            print()