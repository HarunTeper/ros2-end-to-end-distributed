"""Optimization class."""

# import gurobipy as gp
# from gurobipy import GRB

from system import System
from timer import Timer
from subscription import Subscription


class Optimization:
    """Optimization class."""

    system: System
    system = 0

    def __init__(self, system):
        """Initialize optimization."""
        self.system = system

        self.system.nodes = self.system.nodes[1:] # TODO: remove this line
        self.system.chains[0] = self.system.chains[0][1:] # TODO: remove this line
        print('----------------------------------------')
        print()
        print('Optimization:')
        settings = ['nothing','dds', 'executor_policy', 'node_assignment', 'timer_periods', 'fix-assign', 'fix-async', 'fix-sync']
        results = []
        for setting in settings:
            print('----------------------------------------')
            print()
            results.append(self.optimize(setting))
            print()
            print('----------------------------------------')
        for setting, result in zip(settings, results):
            print(setting, result)
        print()
        print('----------------------------------------')

    def optimize(self, setting):
        """Optimize."""
        print('Setting:', setting)
        return

        number_of_nodes = len(self.system.nodes)
        number_of_executors = 0
        if setting == 'node_assignment' or setting == 'fix-async' or setting == 'fix-sync':
            number_of_executors = 8
        else:
            number_of_executors = 8
        subscriptions = [subscription for node in self.system.nodes for subscription in node.subscription_list]
        timers = [timer for node in self.system.nodes for timer in node.timer_list]
        tasks = timers + subscriptions

        # print('Nodes:')
        for node in self.system.nodes:
            print(node.name)

        epsilon = 0.00001

        optimize_dds = False
        optimize_executor_policy = False
        optimize_node_assignment = False
        optimize_timer_periods = False

        if setting == 'dds':
            optimize_dds = True
        elif setting == 'executor_policy':
            optimize_executor_policy = True
        elif setting == 'node_assignment':
            optimize_node_assignment = True
        elif setting == 'timer_periods':
            optimize_timer_periods = True
        elif setting == 'fix-assign':
            optimize_dds = True
            optimize_executor_policy = True
            optimize_timer_periods = True
        elif setting == 'fix-async':
            optimize_node_assignment = True
            optimize_executor_policy = True
            optimize_timer_periods = True
        elif setting == 'fix-sync':
            optimize_node_assignment = True
            optimize_executor_policy = True
            optimize_timer_periods = True

        # create model
        model = gp.Model('optimization')

        # create variables and constraints

        # executor_dds_mode, 0 = asynchronous, 1 = synchronous
        executor_dds_mode = model.addVars(number_of_executors, vtype=GRB.BINARY, name='executor_dds_mode')
        if not optimize_dds:
            if setting == 'fix-async':
                model.addConstrs((executor_dds_mode[executor] == 0 for executor in range(number_of_executors)), name='executor_dds_mode')
            elif setting == 'fix-sync':
                model.addConstrs((executor_dds_mode[executor] == 1 for executor in range(number_of_executors)), name='executor_dds_mode')
            else:
                model.addConstrs((executor_dds_mode[executor] == 1 for executor in range(number_of_executors)), name='executor_dds_mode')

        # executor_task_policy, 0 = timers_first, 1 = subscriptions_first
        executor_task_policy = model.addVars(number_of_executors, vtype=GRB.BINARY, name='executor_task_policy')
        if not optimize_executor_policy:
            model.addConstrs((executor_task_policy[executor] == 0 for executor in range(number_of_executors)), name='executor_task_policy')

        # node_executor_assignment, 1 = node is assigned to executor, 0 = node is not assigned to executor
        node_executor_assignment = model.addVars(number_of_nodes, number_of_executors, vtype=GRB.BINARY, name='node_executor_assignment')
        if not optimize_node_assignment:
            model.addConstrs((gp.quicksum(node_executor_assignment[node, executor] for node in range(number_of_nodes)) <= 1 for executor in range(number_of_executors)), name='node_executor_assignment_sum')
        elif setting == 'node_assignment' or setting == 'fix-async' or setting == 'fix-sync':
            model.addConstr(node_executor_assignment[4, 0] == 1)
            model.addConstr(node_executor_assignment[5, 0] == 1)
            model.addConstr((gp.quicksum(node_executor_assignment[node, 0] for node in range(number_of_nodes)) == 2))
        
        # the sum of the node_executor_assignment variables for each node must be 1
        model.addConstrs((gp.quicksum(node_executor_assignment[node, executor] for executor in range(number_of_executors)) == 1 for node in range(number_of_nodes)), name='node_executor_assignment_sum')

        # timer_period, period of timer
        timer_period = model.addVars(len(timers), lb=0.0, vtype=GRB.CONTINUOUS, name='timer_period')
        if not optimize_timer_periods:
            model.addConstrs((timer_period[timer_index] == timer.period for timer_index, timer in enumerate(timers)), name='timer_period')
        model.addConstr(timer_period[2] == 0.01) # TODO: remove this line

        # task_node_assignment, 1 = task is assigned to node, 0 = task is not assigned to node
        task_node_assignment = model.addVars(len(tasks), number_of_nodes, vtype=GRB.BINARY, name='task_node_assignment')

        # read the task node assignment from the system
        for node_index in range(number_of_nodes):
            for task_index, task in enumerate(tasks):
                if task in self.system.nodes[node_index].timer_list or task in self.system.nodes[node_index].subscription_list:
                    model.addConstr(task_node_assignment[task_index, node_index] == 1)
                else:
                    model.addConstr(task_node_assignment[task_index, node_index] == 0)

        # the sum of task_node_assignment[i,:] must be 1
        model.addConstrs((gp.quicksum(task_node_assignment[task_index, node_index] for node_index in range(number_of_nodes)) == 1 for task_index, task in enumerate(tasks)), name='task_node_assignment')

        # task_executor_assignment, 1 = task is assigned to executor, 0 = task is not assigned to executor
        task_executor_assignment = model.addVars(len(tasks), number_of_executors, vtype=GRB.BINARY, name='task_executor_assignment')

        # set the task_executor_assignment
        for task_index, task in enumerate(tasks):
            for executor_index in range(number_of_executors):
                model.addConstr(task_executor_assignment[task_index, executor_index] == gp.quicksum(task_node_assignment[task_index, node_index] * node_executor_assignment[node_index, executor_index] for node_index in range(number_of_nodes)))
        
        # the sum of task_executor_assignment[i,:] must be 1
        model.addConstrs((gp.quicksum(task_executor_assignment[task_index, executor_index] for executor_index in range(number_of_executors)) == 1 for task_index, _ in enumerate(tasks)), name='task_executor_assignment')

        # task_dds_mode, 0 = asynchronous, 1 = synchronous
        task_dds_mode = model.addVars(len(tasks), vtype=GRB.BINARY, name='task_dds_mode')

        # get the task_dds_mode from the task_executor_assignment and executor_dds_mode
        for task_index, task in enumerate(tasks):
            model.addConstr(task_dds_mode[task_index] == gp.quicksum(task_executor_assignment[task_index, executor_index] * executor_dds_mode[executor_index] for executor_index in range(number_of_executors)))

        # task_task_policy
        task_task_policy = model.addVars(len(tasks), vtype=GRB.BINARY, name='task_task_policy')

        # get the task_task_policy from the task_executor_assignment and executor_task_policy
        for task_index, task in enumerate(tasks):
            for executor_index in range(number_of_executors):
                model.addConstr(task_task_policy[task_index] == gp.quicksum(task_executor_assignment[task_index, executor_index] * executor_task_policy[executor_index] for executor_index in range(number_of_executors)))

        # task executor equality between two tasks
        task_executor_equality = model.addVars(len(tasks), len(tasks), vtype=GRB.BINARY, name='task_executor_equality')

        # get the task_executor_equality from the task_executor_assignment
        for task_index_1, _ in enumerate(tasks):
            for task_index_2, _ in enumerate(tasks):
                if task_index_1 == task_index_2:
                    model.addConstr(task_executor_equality[task_index_1, task_index_2] == 0)
                else:
                    model.addConstr(task_executor_equality[task_index_1, task_index_2] == gp.quicksum(task_executor_assignment[task_index_1, executor_index] * task_executor_assignment[task_index_2, executor_index] for executor_index in range(number_of_executors)))

        # node executor equality
        node_executor_equality = model.addVars(number_of_nodes, number_of_nodes, vtype=GRB.BINARY, name='node_executor_equality')

        # get the node_executor_equality from the node_executor_assignment
        for node_index_1 in range(number_of_nodes):
            for node_index_2 in range(number_of_nodes):
                if node_index_1 == node_index_2:
                    model.addConstr(node_executor_equality[node_index_1, node_index_2] == 0)
                else:
                    model.addConstr(node_executor_equality[node_index_1, node_index_2] == gp.quicksum(node_executor_assignment[node_index_1, executor_index] * node_executor_assignment[node_index_2, executor_index] for executor_index in range(number_of_executors)))

        # node priority binary comparison
        node_priority_comparison = model.addVars(number_of_nodes, number_of_nodes, vtype=GRB.BINARY, name='node_priority_comparison')

        # the sum of node_priority_comparison[i,j] and node_priority_comparison[j,i] must be 1, if both nodes are on the same executor
        model.addConstrs((node_priority_comparison[node_index_1, node_index_2] + node_priority_comparison[node_index_2, node_index_1] == node_executor_equality[node_index_1, node_index_2] for node_index_1 in range(number_of_nodes) for node_index_2 in range(number_of_nodes) if node_index_1 != node_index_2), name='node_priority_comparison')

        # the sum of node_priority_comparison[i,i] must be 0
        model.addConstrs((node_priority_comparison[node_index, node_index] == 0 for node_index in range(number_of_nodes)), name='node_priority_comparison')

        node_priority_transitive = model.addVars(number_of_nodes, number_of_nodes, number_of_nodes, vtype=GRB.BINARY, name='node_priority_transitive')

        # transitively close the node_priority_comparison
        for node_index_1 in range(number_of_nodes):
            for node_index_2 in range(number_of_nodes):
                for node_index_3 in range(number_of_nodes):
                    if node_index_1 != node_index_2 and node_index_2 != node_index_3 and node_index_1 != node_index_3:
                        model.addConstr(node_priority_transitive[node_index_1, node_index_2, node_index_3] == node_priority_comparison[node_index_1, node_index_2]*node_priority_comparison[node_index_2, node_index_3])
                        model.addConstr((node_priority_transitive[node_index_1, node_index_2, node_index_3] == 1) >> (node_priority_comparison[node_index_1, node_index_3] == 1))

        # task priority binary comparison
        task_priority_comparison = model.addVars(len(tasks), len(tasks), vtype=GRB.BINARY, name='task_priority_comparison')

        # the sum of task_priority_comparison[i,j] and task_priority_comparison[j,i] must be 1, if they are different tasks
        model.addConstrs((task_priority_comparison[task_index_1, task_index_2] + task_priority_comparison[task_index_2, task_index_1] == task_executor_equality[task_index_1, task_index_2] for task_index_1, _ in enumerate(tasks) for task_index_2, _ in enumerate(tasks) if task_index_1 != task_index_2), name='task_priority_comparison')

        # the sum of task_priority_comparison[i,i] must be 0
        model.addConstrs((task_priority_comparison[task_index, task_index] == 0 for task_index, _ in enumerate(tasks)), name='task_priority_comparison')

        task_type_zero_priority_comparison = model.addVars(len(tasks), len(tasks), vtype=GRB.BINARY, name='task_type_one_priority_comparison')
        task_type_one_priority_comparison = model.addVars(len(tasks), len(tasks), vtype=GRB.BINARY, name='task_type_two_priority_comparison')

        task_priority_transitive = model.addVars(len(tasks), len(tasks), len(tasks), vtype=GRB.BINARY, name='task_priority_transitive')

        # transitively close the task_priority_comparison
        for task_index_1, task_1 in enumerate(tasks):
            for task_index_2, task_2 in enumerate(tasks):
                # find the node index of task 1
                node_index_1 = -1
                for node_index, node in enumerate(self.system.nodes):
                    if task in node.subscription_list or task in node.timer_list:
                        node_index_1 = node_index
                        break
                # find the node index of task 2
                node_index_2 = -1
                for node_index, node in enumerate(self.system.nodes):
                    if task in node.subscription_list or task in node.timer_list:
                        node_index_2 = node_index
                        break
                if isinstance(task_1, type(task_2)):
                    model.addConstr((node_priority_comparison[node_index_1, node_index_2] == 1) >> (task_priority_comparison[task_index_1, task_index_2] == 1), name='task_priority_comparison')
                elif isinstance(task_1, Timer) and isinstance(task_2, Subscription):
                    model.addConstr(task_type_zero_priority_comparison[task_index_1, task_index_2] == (1-task_task_policy[task_index_1])*task_executor_equality[task_index_1, task_index_2], name='task_priority_comparison')
                    model.addConstr((task_type_zero_priority_comparison[task_index_1, task_index_2] == 1) >> (task_priority_comparison[task_index_1, task_index_2] == 1))
                elif isinstance(task_1, Subscription) and isinstance(task_2, Timer):
                    model.addConstr(task_type_one_priority_comparison[task_index_1, task_index_2] == task_task_policy[task_index_1]*task_executor_equality[task_index_1, task_index_2], name='task_priority_comparison')
                    model.addConstr((task_type_one_priority_comparison[task_index_1, task_index_2] == 1) >> (task_priority_comparison[task_index_1, task_index_2] == 1))
                for task_index_3, _ in enumerate(tasks):
                    if task_index_1 != task_index_2 and task_index_2 != task_index_3 and task_index_1 != task_index_3:
                        model.addConstr(task_priority_transitive[task_index_1, task_index_2, task_index_3] == task_priority_comparison[task_index_1, task_index_2]*task_priority_comparison[task_index_2, task_index_3], name='task_priority_comparison')
                        model.addConstr((task_priority_transitive[task_index_1, task_index_2, task_index_3] == 1) >> (task_priority_comparison[task_index_1, task_index_3] == 1), name='task_priority_comparison')

        # task wcet
        task_wcet = model.addVars(len(tasks), vtype=GRB.CONTINUOUS, name='task_wcet')
        model.addConstrs((task_wcet[task_index] == task.callback.wcet for task_index, task in enumerate(tasks)), name='task_wcet')

        # task wcet sum
        task_wcet_sum = model.addVars(len(tasks), vtype=GRB.CONTINUOUS, name='task_wcet_sum')
        # task_task_communication_cost = model.addVars(len(tasks), len(tasks), vtype=GRB.CONTINUOUS, name='task_task_communication_cost')
        task_task_synchronous_communication_cost = model.addVars(len(tasks), len(tasks), vtype=GRB.CONTINUOUS, name='task_task_synchronous_communication_cost')
        task_task_asynchronous_communication_cost = model.addVars(len(tasks), len(tasks), vtype=GRB.CONTINUOUS, name='task_task_asynchronous_communication_cost')

        for task_index_1, task in enumerate(tasks):
            for task_index_2, _ in enumerate(tasks):
                if task_index_1 != task_index_2:
                    # if task 2 is a subscription and the subscription topic matches a topic of any publisher of task_1
                    if isinstance(tasks[task_index_2], Subscription):
                        if tasks[task_index_2].subscription_topic in [publisher.topic_name for publisher in task.callback.publishers]:
                            publisher = [publisher for publisher in task.callback.publishers if publisher.topic_name == tasks[task_index_2].subscription_topic][0]
                            model.addConstr(task_task_synchronous_communication_cost[task_index_1, task_index_2] == task_dds_mode[task_index_1] * (1-task_executor_equality[task_index_1, task_index_2]) * publisher.dds_latency)
                            model.addConstr(task_task_asynchronous_communication_cost[task_index_1, task_index_2] == (1-task_dds_mode[task_index_1]) * (1-task_executor_equality[task_index_1, task_index_2]) * publisher.dds_latency)
                        else:
                            model.addConstr(task_task_synchronous_communication_cost[task_index_1, task_index_2] == 0)
                    else:
                        model.addConstr(task_task_synchronous_communication_cost[task_index_1, task_index_2] == 0)
            model.addConstr(task_wcet_sum[task_index_1] == task.callback.wcet + gp.quicksum(task_task_synchronous_communication_cost[task_index_1, task_index_2] for task_index_2, _ in enumerate(tasks) if task_index_1 != task_index_2), name='task_wcet_sum')

        # executor wcet sum
        executor_wcet_sum = model.addVars(number_of_executors, vtype=GRB.CONTINUOUS, name='executor_wcet_sum')
        for executor_index in range(number_of_executors):
            model.addConstr(executor_wcet_sum[executor_index] == gp.quicksum(task_wcet_sum[task_index] * task_executor_assignment[task_index, executor_index] for task_index, _ in enumerate(tasks)), name='executor_wcet_sum')

        # task executor wcet sum
        task_executor_wcet_sum = model.addVars(len(tasks), vtype=GRB.CONTINUOUS, name='task_executor_wcet_sum')
        for task_index, _ in enumerate(tasks):
            model.addConstr(task_executor_wcet_sum[task_index] == gp.quicksum(executor_wcet_sum[executor_index] * task_executor_assignment[task_index, executor_index] for executor_index in range(number_of_executors)), name='task_executor_wcet_sum')

        # higher priority task wcet sum
        higher_priority_task_wcet_sum = model.addVars(len(tasks), vtype=GRB.CONTINUOUS, name='higher_priority_task_wcet_sum')
        for task_index_1, _ in enumerate(tasks):
                model.addConstr(higher_priority_task_wcet_sum[task_index_1] == gp.quicksum(task_wcet_sum[task_index_2] * task_priority_comparison[task_index_2, task_index_1] for task_index_2, _ in enumerate(tasks) if task_index_1 != task_index_2), name='higher_priority_task_wcet_sum')

        # lower priority task wcet sum
        lower_priority_task_wcet_sum = model.addVars(len(tasks), vtype=GRB.CONTINUOUS, name='lower_priority_task_wcet_sum')
        for task_index_1, _ in enumerate(tasks):
                model.addConstr(lower_priority_task_wcet_sum[task_index_1] == gp.quicksum(task_wcet_sum[task_index_2] * task_priority_comparison[task_index_1, task_index_2] for task_index_2, _ in enumerate(tasks) if task_index_1 != task_index_2), name='lower_priority_task_wcet_sum')

        # zero period timer variable
        zero_period_timer = model.addVars(len(timers), vtype=GRB.BINARY, name='zero_period_timer')
        model.addConstrs((zero_period_timer[timer_index] == 1) >> (timer_period[timer_index] == 0) for timer_index, _ in enumerate(timers))
        model.addConstrs((zero_period_timer[timer_index] == 0) >> (timer_period[timer_index] >= epsilon) for timer_index, _ in enumerate(timers))

        # zero period higher priority timer variable
        zero_period_higher_priority = model.addVars(len(timers), vtype=GRB.BINARY, name='zero_period_higher_priority')

        # zero period lower priority timer variable
        zero_period_lower_priority = model.addVars(len(timers), vtype=GRB.BINARY, name='zero_period_lower_priority')

        # chain variables
        chains = self.system.chains
        chain_upper_bound = model.addVars(len(chains), vtype=GRB.CONTINUOUS, name='chain_upper_bound')
        for chain in chains:
            chain_element_upper_bound = model.addVars(len(chain), vtype=GRB.CONTINUOUS, name='chain_element_upper_bound')

        # for every task, create a continuous variable for a sum with lower bound infinity
        until_start_case = model.addVars(len(tasks), lb=-GRB.INFINITY, vtype=GRB.CONTINUOUS, name='until_start_case')
        until_start_sum = model.addVars(len(tasks), lb=-GRB.INFINITY, vtype=GRB.CONTINUOUS, name='until_start_sum')

        # add var zero
        zero = model.addVars((1),vtype=GRB.CONTINUOUS, name='zero')
        model.addConstr(zero[0] == 0)

        # chain upper bound constraint
        for chain_index, chain in enumerate(chains):
            for task_index, task in enumerate(chain):
                if isinstance(task, Timer):
                    task_timer_index = timers.index(task)
                    task_task_index = tasks.index(task)
                    until_start_zero_period_sensor = 0
                    until_start_zero_period_higher_priority = 0
                    until_start_zero_period_lower_priority = 0
                    until_start_non_zero_period = 0
                    until_finish_synchronous = 0
                    until_finish_asynchronous = 0
                    if len(task.callback.read_buffers) == 0:
                        until_start_zero_period_sensor = zero_period_timer[task_timer_index] * task_executor_wcet_sum[task_task_index]
                    else:
                        previous_task_task_index = tasks.index(chain[task_index-1])
                        model.addConstr(zero_period_higher_priority[task_timer_index] == zero_period_timer[task_timer_index] * task_priority_comparison[previous_task_task_index, task_task_index])
                        model.addConstr(zero_period_lower_priority[task_timer_index] == zero_period_timer[task_timer_index] * task_priority_comparison[task_task_index, previous_task_task_index])
                        # Lemma VI.3
                        until_start_zero_period_higher_priority = zero_period_higher_priority[task_timer_index] * (higher_priority_task_wcet_sum[task_task_index] - higher_priority_task_wcet_sum[previous_task_task_index] - task_wcet_sum[previous_task_task_index])
                        until_start_zero_period_lower_priority = zero_period_lower_priority[task_timer_index] * (lower_priority_task_wcet_sum[previous_task_task_index] + higher_priority_task_wcet_sum[task_task_index])
                    # Lemma VI.2
                    model.addConstr(until_start_sum[task_task_index] == timer_period[task_timer_index]-task_wcet_sum[task_task_index]+higher_priority_task_wcet_sum[task_task_index])
                    model.addConstr(until_start_case[task_task_index] == gp.max_(zero[0],until_start_sum[task_task_index]))
                    until_start_non_zero_period = (1-zero_period_timer[task_timer_index]) * (task_executor_wcet_sum[task_task_index]+until_start_case[task_task_index])
                    # Lemma VI.1
                    until_finish_synchronous = task_dds_mode[task_task_index] * task_wcet_sum[task_task_index]
                    # if not last task
                    if task_index != len(chain)-1:
                        next_task_task_index = tasks.index(chain[task_index+1])
                        # Lemma VI.1
                        until_finish_asynchronous = (1-task_dds_mode[task_task_index]) * (task.callback.wcet + task_task_asynchronous_communication_cost[task_task_index, next_task_task_index])
                    model.addConstr(chain_element_upper_bound[task_index] == until_start_zero_period_sensor + until_start_zero_period_higher_priority + until_start_zero_period_lower_priority + until_start_non_zero_period + until_finish_synchronous + until_finish_asynchronous)
                if isinstance(task, Subscription):
                    task_task_index = tasks.index(task)
                    previous_task_task_index = tasks.index(chain[task_index-1])
                    # Lemma VI.4
                    model.addConstr(until_start_sum[task_task_index] == higher_priority_task_wcet_sum[task_task_index] - task_wcet_sum[task_task_index])
                    model.addConstr(until_start_case[task_task_index] == gp.max_(zero[0],until_start_sum[task_task_index]))
                    until_start_executor_non_equal = (1-task_executor_equality[previous_task_task_index, task_task_index]) * (task.dds_buffer.buffer_size * task_executor_wcet_sum[task_task_index])+until_start_case[task_task_index]
                    # Lemma VI.5
                    until_start_executor_equal = task_executor_equality[previous_task_task_index, task_task_index] * (lower_priority_task_wcet_sum[previous_task_task_index] + higher_priority_task_wcet_sum[task_task_index])
                    # Lemma VI.1
                    until_finish_synchronous = task_dds_mode[task_task_index] * task_wcet_sum[task_task_index]
                    # if not last task
                    until_finish_asynchronous = 0
                    if task_index != len(chain)-1:
                        next_task_task_index = tasks.index(chain[task_index+1])
                        # Lemma VI.1
                        until_finish_asynchronous = (1-task_dds_mode[task_task_index]) * (task.callback.wcet + task_task_asynchronous_communication_cost[task_task_index, next_task_task_index])
                    model.addConstr(chain_element_upper_bound[task_index] == until_start_executor_non_equal + until_start_executor_equal + until_finish_synchronous + until_finish_asynchronous)
            model.addConstr(chain_upper_bound[chain_index] == gp.quicksum(chain_element_upper_bound[task_index] for task_index, _ in enumerate(chain)))
        # total chain upper bound variable
        total_chain_upper_bound = model.addVars((1),vtype=GRB.CONTINUOUS, name='total_chain_upper_bound')

        # total chain upper bound constraint
        model.addConstr(total_chain_upper_bound[0] == gp.quicksum(chain_upper_bound[chain_index] for chain_index, _ in enumerate(chains)))

        # objective function
        model.setObjective(gp.quicksum(total_chain_upper_bound), GRB.MINIMIZE)

        # solve model
        model.optimize()

        # check if model is feasible
        if model.status == GRB.INFEASIBLE:
            print('Model is infeasible')
            model.computeIIS()
            model.write("failed.ilp")
            return False

        # check if model is unbounded
        if model.status == GRB.UNBOUNDED:
            print('Model is unbounded')
            return False

        # check if model is optimal
        if model.status == GRB.OPTIMAL:
            print('Model is optimal')
            print()
            print("----------------------------------------")
            print()
            # # Print all Variables
            # for index, node in enumerate(self.nodes):
            #     print(index, node.name)
            # for index, callback in enumerate(tasks):
            #     print(index, callback, self.find_node_index(self.nodes, callback))

            executor_node_lists = []
            for _ in range(number_of_executors):
                executor_node_lists.append([])

            node_timer_lists =[]
            for node in self.system.nodes:
                node_timer_lists.append(node.timer_list)

            node_subscription_lists = []
            for node in self.system.nodes:
                node_subscription_lists.append(node.subscription_list)

            node_priority_comparison_variables = []
            for _ in range(number_of_nodes):
                inner_list = []
                for _ in range(number_of_nodes):
                    inner_list.append(None)
                node_priority_comparison_variables.append(inner_list)

            task_priority_comparison_variables = []
            for _ in range(len(tasks)):
                inner_list = []
                for _ in range(len(tasks)):
                    inner_list.append(None)
                task_priority_comparison_variables.append(inner_list)

            for var in model.getVars():
                if "transitive" not in var.varName:
                    # if var.X != 0:
                    #     print(var.varName, var.X)

                # split var name by [ and ]
                    var_name = var.varName.split("[")[0]
                    var_indices = var.varName.split("[")[1].split("]")[0]
                    #create a list of var_indices by splitting using ,
                    var_indices = var_indices.split(",")


                    if var_name == 'executor_dds_mode':
                        print('Executor DDS Mode:', var_indices, ['asynchronous', 'synchronous'][int(var.X)])
                    if var_name == 'executor_task_policy':
                        print('Executor Task Policy:', var_indices, ['timers_before_subscriptions', 'subscriptions_before_timers'][int(var.X)])
                    if var_name == 'node_executor_assignment':
                        if var.X == 1:
                            print('Node Executor Assignment:', self.system.nodes[int(var_indices[0])].name, 'is assigned to Executor', int(var_indices[1]))
                            executor_node_lists[int(var_indices[1])].append(self.system.nodes[int(var_indices[0])])
                    if var_name == 'timer_period':
                        timer = timers[int(var_indices[0])]
                        timer_node = 0
                        timer_index = 0
                        for node_index, node in enumerate(self.system.nodes):
                            if timer in node.timer_list:
                                timer_node = node
                                timer_index = node.timer_list.index(timer)
                        print('Timer', timer_index, 'of Node', timer_node.name, 'has period', var.X)
                    if var_name == 'node_priority_comparison':
                        if var.X == 1:
                            print('Node', self.system.nodes[int(var_indices[0])].name, 'has higher priority than Node', self.system.nodes[int(var_indices[1])].name)
                        node_priority_comparison_variables[int(var_indices[0])][int(var_indices[1])] = var.X
                    if var_name == 'task_priority_comparison':
                        if var.X == 1:
                            print('Task', int(var_indices[0]), 'has higher priority than Task', int(var_indices[1]))
                        task_priority_comparison_variables[int(var_indices[0])][int(var_indices[1])] = var.X
            # use the node_priority_comparison_variables to create a list of nodes ordered by priority
            for executor_node_list in executor_node_lists:
                # sort each list using the node_priority_comparison_variables
                executor_node_list.sort(key=lambda x: sum(node_priority_comparison_variables[self.system.nodes.index(x)]), reverse=True)
            for node_timer_list in node_timer_lists:
                node_timer_list.sort(key=lambda x: sum(task_priority_comparison_variables[tasks.index(x)]), reverse=True)
            for node_subscription_list in node_subscription_lists:
                node_subscription_list.sort(key=lambda x: sum(task_priority_comparison_variables[tasks.index(x)]), reverse=True)
            
            for executor_node_list_index, executor_node_list in enumerate(executor_node_lists):
                print('Executor Node List', executor_node_list_index, ':', [(node.name, self.system.nodes.index(node)) for node in executor_node_list])
            for node_timer_list_index, node_timer_list in enumerate(node_timer_lists):
                print('Node', self.system.nodes[node_timer_list_index].name, 'Timer List:', [timer for timer in node_timer_list])
            for node_subscription_list_index, node_subscription_list in enumerate(node_subscription_lists):
                print('Node', self.system.nodes[node_subscription_list_index].name, 'Subscription List:', [subscription for subscription in node_subscription_list])

            print('Obj:', model.objVal)

            return model.objVal



