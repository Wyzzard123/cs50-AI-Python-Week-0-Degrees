import csv
import sys

from util import Node, StackFrontier, QueueFrontier

# Maps names to a set of corresponding person_ids
names = {}

# Maps person_ids to a dictionary of: name, birth, movies (a set of movie_ids)
people = {}

# Maps movie_ids to a dictionary of: title, year, stars (a set of person_ids)
movies = {}


def load_data(directory):
    """
    Load data from CSV files into memory.
    """
    # Load people
    with open(f"{directory}/people.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            people[row["id"]] = {
                "name": row["name"],
                "birth": row["birth"],
                "movies": set()
            }
            if row["name"].lower() not in names:
                names[row["name"].lower()] = {row["id"]}
            else:
                names[row["name"].lower()].add(row["id"])

    # Load movies
    with open(f"{directory}/movies.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            movies[row["id"]] = {
                "title": row["title"],
                "year": row["year"],
                "stars": set()
            }

    # Load stars
    with open(f"{directory}/stars.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                people[row["person_id"]]["movies"].add(row["movie_id"])
                movies[row["movie_id"]]["stars"].add(row["person_id"])
            except KeyError:
                pass


def main():
    if len(sys.argv) > 2:
        sys.exit("Usage: python degrees.py [directory]")
    directory = sys.argv[1] if len(sys.argv) == 2 else "large"

    # Load data from files into memory
    print("Loading data...")
    load_data(directory)
    print("Data loaded.")

    source = person_id_for_name(input("Name: "))
    if source is None:
        sys.exit("Person not found.")
    target = person_id_for_name(input("Name: "))
    if target is None:
        sys.exit("Person not found.")

    path = shortest_path(source, target)

    if path is None:
        print("Not connected.")
    else:
        degrees = len(path)
        print(f"{degrees} degrees of separation.")
        path = [(None, source)] + path
        for i in range(degrees):
            person1 = people[path[i][1]]["name"]
            person2 = people[path[i + 1][1]]["name"]
            movie = movies[path[i + 1][0]]["title"]
            print(f"{i + 1}: {person1} and {person2} starred in {movie}")


def shortest_path(source, target):
    """
    Returns the shortest list of (movie_id, person_id) pairs
    that connect the source to the target.

    If no possible path, returns None.
    """
    from collections import deque

    class Node:
        def __init__(self, current_tuple, parent_node):
            # To get the path. current_tuple is
            self.current_tuple = current_tuple
            self.current_person_id = current_tuple[1]
            self.current_movie_id = current_tuple[0]
            # The first tuple after the source will have no parent_node, ie None.
            self.parent_node = parent_node

        def __str__(self):
            return f"{self.current_tuple} - {movies[self.current_movie_id]['title']} - {people[self.current_person_id]['name']}"

    class StackFrontier():
        def __init__(self):
            self.frontier = []

        def add(self, node):
            self.frontier.append(node)

        # def extend(self, nodes):
        #     # Extend by a list of nodes
        #     self.frontier.extend(nodes)

        def contains_tuple(self, current_tuple):
            return any(node.current_tuple == current_tuple for node in self.frontier)

        def contains_current_person_id(self, current_person_id):
            return any(node.current_person_id == current_person_id for node in self.frontier)

        # def contains_state(self, state):
        #     return any(node.state == state for node in self.frontier)

        def empty(self):
            return len(self.frontier) == 0

        def remove(self):
            if self.empty():
                raise Exception("empty frontier")
            else:
                node = self.frontier[-1]
                self.frontier = self.frontier[:-1]
                return node

    class QueueFrontier(StackFrontier):

        def remove(self):
            if self.empty():
                raise Exception("empty frontier")
            else:
                node = self.frontier[0]
                self.frontier = self.frontier[1:]
                return node

    if not people[source]["movies"]:
        print(people[source]["name"], "has not starred in any movies")
        return None

    if not people[target]["movies"]:
        # If the source or target have not starred in any movies at all, immediately return None
        print(people[target]["name"], "has not starred in any movies")
        return None

    # Use BFS to ensure we get the shortest path, so use a deque, which is Python's ipmlementation of a queue.
    # Add neighbours to the frontier.
    # Going from source to target
    frontier = QueueFrontier()
    # Going from target to source
    frontier_reverse = QueueFrontier()

    explored_ids = set()
    explored_ids_reversed = set()

    # Make sure the explored_id includes the source
    explored_ids.add(source)
    explored_ids_reversed.add(target)

    neighbors = neighbors_for_person(source)
    for neighbor in neighbors:
        if neighbor[1] == target:
            # If the person_id in the tuple is the target, then just the neighbor tuple alone is our shortest path.
            return [neighbor]
        else:
            # Otherwise, add the neighbor to the frontier
            frontier.add(Node(current_tuple=neighbor, parent_node=None))
    # TODO - Reverse
    # Go backwards and forwards at the same time
    neighbors_reverse = neighbors_for_person(target)

    for neighbor in neighbors_reverse:
        # No need to check for target as we have already done that above in the forward check.
        # Otherwise, add the neighbor to the frontier. Right now, parent_node is None.
        frontier_reverse.add(Node(current_tuple=neighbor, parent_node=None))

    # Contain reverse nodes with person_id as key
    reverse_node_dict = {}

    # stop reversing once we hit a point where the explored IDs coincide
    stop_reversing = False
    continue_loop_despite_stop_reversing = False
    # Implement breadth first search
    while True:

        # If the frontier is empty and we haven't reached the target, there is no possible path.
        if not frontier.frontier:
            print("No frontier")
            return None

        if not stop_reversing:
            # Backwards
            if not frontier_reverse.frontier:
                print("No reverse frontier")
                return None

        # Remove first node
        current_node = frontier.remove()
        print("Current Node:", current_node)

        # Add to explored
        explored_ids.add(current_node.current_person_id)

        if not stop_reversing:
            # Remove reverse first node
            current_node_reverse = frontier_reverse.remove()
            reverse_node_dict[current_node.current_person_id] = current_node_reverse
            print("Current Node Reverse:", current_node_reverse)

            explored_ids_reversed.add(current_node_reverse.current_person_id)

        neighbors_of_current_node = neighbors_for_person(current_node.current_person_id)

        if not stop_reversing:
            neighbors_of_current_node_reverse = neighbors_for_person(current_node_reverse.current_person_id)

        for neighbor in neighbors_of_current_node:
            if neighbor[1] in explored_ids or frontier.contains_current_person_id(neighbor[1]):
                # Checking if person's id has already been explored.
                continue
            # Convert neighbor into a node
            neighbor_node = Node(current_tuple=neighbor, parent_node=current_node)
            print("Neighbor Node:", neighbor_node)
            if neighbor[1] == target:
                # If the neighbor is the target, we create a list of neighbors going back
                latest_node = neighbor_node
                reversed_shortest_path = []
                while latest_node.parent_node is not None:
                    # Once parent_node is None, we have reached the first node.
                    reversed_shortest_path.append(latest_node.current_tuple)
                    latest_node = latest_node.parent_node

                # Return the shortest path
                return reversed_shortest_path[::-1]
            else:
                if neighbor_node.current_person_id not in explored_ids and not frontier.contains_current_person_id(neighbor_node.current_person_id):
                    frontier.add(neighbor_node)
                if neighbor_node.current_person_id in explored_ids_reversed:
                    print("IN EXPLORED IDS REVERSED")
                    # Here, add this person to the path instead.
                    # first_reverse_node = reverse_node_dict[current_node_reverse.current_person_id]
                    first_reverse_node = reverse_node_dict.get(current_node_reverse.current_person_id, None)
                    if first_reverse_node is None:
                        print("No such key", current_node_reverse.current_person_id)
                        print(f"This is {people[current_node_reverse.current_person_id]['name']}")
                        print("Continuing loop")
                        # If there is no such key, we're probably already at the target. Just continue the outer while loop, but don't do any more reverses.
                        stop_reversing = True
                        continue_loop_despite_stop_reversing = True
                        break
                    else:
                        first_reverse_node_converted = Node(current_tuple=first_reverse_node.current_tuple, parent_node=neighbor_node)
                        # Going backwards in the reversed nodes
                        first_reverse_node_parent = first_reverse_node.parent_node
                        stop_reversing = True
                        break

        if stop_reversing and not continue_loop_despite_stop_reversing:
            current_node = first_reverse_node_converted
            current_node_reversed = first_reverse_node
            while current_node_reversed.parent_node is not None:
                current_node_reversed = current_node_reversed.parent_node
                current_node = Node(current_tuple=current_node_reversed.current_tuple, parent_node=current_node)

            # Once parent node is none, do the usual finding of neighbors for the final node.
            final_neighbors = neighbors_for_person(current_node.current_person_id)
            for neighbor in final_neighbors:
                if neighbor[1] == target:
                    neighbor_node = Node(current_tuple=neighbor, parent_node=current_node)
                    latest_node = neighbor_node
                    reversed_shortest_path = []
                    while latest_node.parent_node is not None:
                        # Once parent_node is None, we have reached the first node.
                        reversed_shortest_path.append(latest_node.current_tuple)
                        latest_node = latest_node.parent_node
                    # Return the shortest path
                    return reversed_shortest_path[::-1]

        if not stop_reversing:
            # In reverse
            for neighbor in neighbors_of_current_node_reverse:
                if neighbor[1] in explored_ids or frontier.contains_current_person_id(neighbor[1]):
                    # Checking if person's id has already been explored.
                    continue
                neighbor_node_reverse = Node(current_tuple=neighbor, parent_node=current_node_reverse)
                print("Neighbor reverse node:", neighbor_node_reverse)
                if neighbor[1] == source:
                    latest_node_reverse = neighbor_node_reverse
                    shortest_path = []
                    # TODO - Last node is not included now
                    while latest_node_reverse.parent_node is not None:
                        shortest_path.append(latest_node_reverse.current_tuple)
                        latest_node_reverse = latest_node_reverse.parent_node
                    # Ignore first tuple as that includes the source.
                    return shortest_path[1:]
                else:
                    if neighbor_node_reverse.current_person_id not in explored_ids_reversed and not frontier_reverse.contains_current_person_id(neighbor_node_reverse.current_person_id):
                        frontier_reverse.add(neighbor_node_reverse)
                        reverse_node_dict[neighbor_node_reverse.current_person_id] = neighbor_node_reverse
                    if neighbor_node_reverse.current_person_id in explored_ids:
                        print("IN EXPLORED IDS")
                        return None
                        break





def person_id_for_name(name):
    """
    Returns the IMDB id for a person's name,
    resolving ambiguities as needed.
    """
    person_ids = list(names.get(name.lower(), set()))
    if len(person_ids) == 0:
        return None
    elif len(person_ids) > 1:
        print(f"Which '{name}'?")
        for person_id in person_ids:
            person = people[person_id]
            name = person["name"]
            birth = person["birth"]
            print(f"ID: {person_id}, Name: {name}, Birth: {birth}")
        try:
            person_id = input("Intended Person ID: ")
            if person_id in person_ids:
                return person_id
        except ValueError:
            pass
        return None
    else:
        return person_ids[0]


def neighbors_for_person(person_id):
    """
    Returns (movie_id, person_id) pairs for people
    who starred with a given person.
    """
    movie_ids = people[person_id]["movies"]
    neighbors = set()
    for movie_id in movie_ids:
        for person_id in movies[movie_id]["stars"]:
            neighbors.add((movie_id, person_id))
    return neighbors


if __name__ == "__main__":
    main()
