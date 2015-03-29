#!/usr/bin/env python
import random
import logging


class CapacityError(Exception):
    pass


class MaxPerNodeScheduler(object):
    """A simple node aware scheduler."""
    def __init__(self, startup_func, shutdown_func, list_running_by_node_func, is_healthy_func, max_per_node=1):
        """
        Args:
            startup_func (function): A callback function for container startup that takes an argument of a node to start on and returns True on success and False on failure.
                                     The resulting instance MUST return True when passed into list_running_by_node_func.
            shutdown_func (function): A callback function for container shutdown that takes an argument of an instance id to stop returns True on success and False on failure.
            list_running_by_node_func (function): A callback function that returns a dictionary of nodes as keys and running instances on said nodes as values.
                                                  If the dictionary is ordered startups will favour the first and shutdown will favour the last nodes. This allows for example ordering by free slots. You probably don't want to count the size of your apps slots against the total running tho to avoid it flapping between similarly loaded servers, so likely you want "free slots += slots used by your app" to keep things sane.
            is_healthy_func (function): A callback function that takes an argument of an instance and returns True for a healthy instance and False for an unhealthy one.
        Returns:
            an instance of SimpleNodeScheduler.
        """
        self.startup_func = startup_func
        self.shutdown_func = shutdown_func
        self.list_running_by_node_func = list_running_by_node_func
        self.is_healthy_func = is_healthy_func
        self.changed = False
        self.success = False
        self.max_per_node = max_per_node
        self.logger = logging.getLogger(__name__)

    def __update_instances_by_node(self):
        self.running_instances_by_node = self.list_running_by_node_func()
        return True

    def __enough_instances(self, desired_qty):
        self.logger.debug('Currently have {} containers, we should have {} containers'.format(len([i for ni in self.running_instances_by_node.values() for i in ni]), desired_qty))
        if len([i for ni in self.running_instances_by_node.values() for i in ni]) < desired_qty:
            chosen_node = sorted(self.running_instances_by_node.items(), key=lambda (k, v): len(v))[0][0]
            if len(self.running_instances_by_node[chosen_node]) == self.max_per_node:
                raise CapacityError()
            self.startup_func(chosen_node)
            self.changed = True
            self.__update_instances_by_node()
            return False
        else:
            return True

    def __correctly_configured(self):
        def healthcheck_nodes_with_exceptions_as_False():
            for instances in self.running_instances_by_node.values():
                for instance in instances:
                    try:
                        healthy = self.is_healthy_func(instance)
                    except Exception as e:
			print e.message
                        healthy = False
                    if not healthy:
                        yield instance
        try:
            bad_instance = healthcheck_nodes_with_exceptions_as_False().next()
            self.shutdown_func(bad_instance)
            self.__update_instances_by_node()
            self.changed = True
            return False
        except StopIteration:
            return True
        except Exception:
            return False

    def __too_many_instances(self, desired_qty):
        instance_counts = sorted([(iby[0], len(iby[1])) for iby in self.running_instances_by_node.items()], key=lambda v: v[1])
        if abs(instance_counts[0][1] - instance_counts[-1][1]) > 1 or sum(map(lambda i: i[1], instance_counts)) > desired_qty:
            remove_from_node = instance_counts[-1][0]
            bad_instance = random.choice(self.running_instances_by_node[remove_from_node])
            self.shutdown_func(bad_instance)
            self.__update_instances_by_node()
            self.changed = True
            return False
        else:
            return True

    def __unbalanced_instances(self, desired_qty):
        gap_found = False
        node_to_stop = None
        for node, instances in self.running_instances_by_node.items():
            if not instances:
                gap_found = True
            elif gap_found and instances:
                node_to_stop = instances[-1]
        if gap_found and node_to_stop:
            self.changed = True
            self.shutdown_func(node_to_stop)
            return False
        else:
            return True

    def run(self, desired_qty):
        self.running_instances_by_node = self.list_running_by_node_func()

        double_expected_max_iterations = max(len([i for ni in self.running_instances_by_node.values() for i in ni]) * 2, desired_qty * 2)
	print double_expected_max_iterations

        # If double_expected_max_iterations is 0 that means we want 0 instances and we're already there, so return True
        if double_expected_max_iterations == 0:
            self.success = True
            return

        while double_expected_max_iterations > 0:
            double_expected_max_iterations -= 1
            # Enough instances?
            if not self.__enough_instances(desired_qty):
                yield ("started_instances", "there weren't enough")
                continue

            # All correctly configured?
            if not self.__correctly_configured():
                yield ("stopped_instances", "badly configured or failed healthcheck")
                continue

            # Unbalanced instances?
            #if not self.__unbalanced_instances(desired_qty):
            #    yield ("stopped_instances", "unbalanced")
            #    continue

            # Too many instances on a node or on all nodes?
            if not self.__too_many_instances(desired_qty):
                yield ("stopped_instances", "too many")
                continue

            self.success = True
            return

        self.success = False

        return
