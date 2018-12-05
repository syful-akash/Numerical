# # from itertools import permutations
# #
# # def ingroup_generator(species, n):
# #     for perm in permutations(species, n):
# #         yield tuple([tuple(perm), tuple(s for s in species if s not in perm)])
# #
# # def format_newick(s, outgroup=''):
# #     return '(' + ', '.join('({})'.format(', '.join(p)) for p in s) + ',({}));'.format(outgroup)
# # def Remove(duplicate):
# #     final_list = []
# #     for num in duplicate:
# #         if num not in final_list:
# #             final_list.append(num)
# #     return final_list
# # species = ["1","1","1","1","1"]
# # outgroup = "0"
# # ingroup = [s for s in species if s != outgroup]
# #
# # itertools_newicks= []
# # for n in range(1, len(ingroup)):
# #     for p in ingroup_generator(ingroup, n):
# #         itertools_newicks.append(format_newick(p, outgroup))
# #
# # for newick in itertools_newicks:
# #     print(newick)
#
#
#
#
#
#
#
#

# from itertools import product
# # According to https://stackoverflow.com/a/30134039/1878788:
# # The problem is solved recursively:
# # If you already have a partition of n-1 elements, how do you use it to partition n elements?
# # Either place the n'th element in one of the existing subsets, or add it as a new, singleton subset.
# def partitions_of_set(s):
#     if len(s) == 1:
#         yield frozenset(s)
#         return
#     # Extract one element from the set
#     # https://stackoverflow.com/a/43804050/1878788
#     elem, *_ = s
#     rest = frozenset(s - {elem})
#     for partition in partitions_of_set(rest):
#         for subset in partition:
#             # Insert the element in the subset
#             try:
#                 augmented_subset = frozenset(subset | frozenset({elem}))
#             except TypeError:
#                 # subset is actually an atomic element
#                 augmented_subset = frozenset({subset} | frozenset({elem}))
#             yield frozenset({augmented_subset}) | (partition - {subset})
#         # Case with the element in its own extra subset
#         yield frozenset({elem}) | partition
# def trees(leaves):
#     if type(leaves) not in (set, frozenset):
#         # It actually is a single leaf
#         yield leaves
#         # Don't try to yield any more trees
#         return
#     # Otherwise, we will have to consider all the possible
#     # partitions of the set of leaves, and for each partition,
#     # construct the possible trees for each part
#     for partition in partitions_of_set(leaves):
#         # We need to skip the case where the partition
#         # has only one subset (the initial set itself),
#         # otherwise we will try to build an infinite
#         # succession of nodes with just one subtree
#         if len(partition) == 1:
#             part, *_ = partition
#             # Just to be sure the assumption is correct
#             # part == leaves
#             continue
#         # We recursively apply *tree* to each part
#         # and obtain the possible trees by making
#         # the product of the sets of possible subtrees.
#         for subtree in product(*map(trees, partition)):
#             # Using a frozenset guarantees
#             # that there will be no duplicates
#             yield frozenset(subtree)
# def print_set(f):
#     if type(f) not in (set, frozenset):
#         return str(f)
#     return "(" + ",".join(sorted(map(print_set, f))) + ")"
# all_trees = frozenset(
#     {frozenset({tree, "0"}) for tree in trees({"1", "2", "3"})})
#
# for tree in all_trees:
#     print(print_set(tree) + ";")
#
#
#
#
#
#
#
#
#
#
#
#
#
import bisect
import itertools
import operator

class _BNode(object):
    __slots__ = ["tree", "contents", "children"]

    def __init__(self, tree, contents=None, children=None):
        self.tree = tree
        self.contents = contents or []
        self.children = children or []
        if self.children:
            assert len(self.contents) + 1 == len(self.children), \
                    "one more child than data item required"

    def __repr__(self):
        name = getattr(self, "children", 0) and "Branch" or "Leaf"
        return "<%s %s>" % (name, ", ".join(map(str, self.contents)))

    def lateral(self, parent, parent_index, dest, dest_index):
        if parent_index > dest_index:
            dest.contents.append(parent.contents[dest_index])
            parent.contents[dest_index] = self.contents.pop(0)
            if self.children:
                dest.children.append(self.children.pop(0))
        else:
            dest.contents.insert(0, parent.contents[parent_index])
            parent.contents[parent_index] = self.contents.pop()
            if self.children:
                dest.children.insert(0, self.children.pop())

    def shrink(self, ancestors):
        parent = None

        if ancestors:
            parent, parent_index = ancestors.pop()
            # try to lend to the left neighboring sibling
            if parent_index:
                left_sib = parent.children[parent_index - 1]
                if len(left_sib.contents) < self.tree.order:
                    self.lateral(
                            parent, parent_index, left_sib, parent_index - 1)
                    return

            # try the right neighbor
            if parent_index + 1 < len(parent.children):
                right_sib = parent.children[parent_index + 1]
                if len(right_sib.contents) < self.tree.order:
                    self.lateral(
                            parent, parent_index, right_sib, parent_index + 1)
                    return

        center = len(self.contents) // 2
        sibling, push = self.split()

        if not parent:
            parent, parent_index = self.tree.BRANCH(
                    self.tree, children=[self]), 0
            self.tree._root = parent

        # pass the median up to the parent
        parent.contents.insert(parent_index, push)
        parent.children.insert(parent_index + 1, sibling)
        if len(parent.contents) > parent.tree.order:
            parent.shrink(ancestors)

    def grow(self, ancestors):
        parent, parent_index = ancestors.pop()

        minimum = self.tree.order // 2
        left_sib = right_sib = None

        # try to borrow from the right sibling
        if parent_index + 1 < len(parent.children):
            right_sib = parent.children[parent_index + 1]
            if len(right_sib.contents) > minimum:
                right_sib.lateral(parent, parent_index + 1, self, parent_index)
                return

        # try to borrow from the left sibling
        if parent_index:
            left_sib = parent.children[parent_index - 1]
            if len(left_sib.contents) > minimum:
                left_sib.lateral(parent, parent_index - 1, self, parent_index)
                return

        # consolidate with a sibling - try left first
        if left_sib:
            left_sib.contents.append(parent.contents[parent_index - 1])
            left_sib.contents.extend(self.contents)
            if self.children:
                left_sib.children.extend(self.children)
            parent.contents.pop(parent_index - 1)
            parent.children.pop(parent_index)
        else:
            self.contents.append(parent.contents[parent_index])
            self.contents.extend(right_sib.contents)
            if self.children:
                self.children.extend(right_sib.children)
            parent.contents.pop(parent_index)
            parent.children.pop(parent_index + 1)

        if len(parent.contents) < minimum:
            if ancestors:
                # parent is not the root
                parent.grow(ancestors)
            elif not parent.contents:
                # parent is root, and its now empty
                self.tree._root = left_sib or self

    def split(self):
        center = len(self.contents) // 2
        median = self.contents[center]
        sibling = type(self)(
                self.tree,
                self.contents[center + 1:],
                self.children[center + 1:])
        self.contents = self.contents[:center]
        self.children = self.children[:center + 1]
        return sibling, median

    def insert(self, index, item, ancestors):
        self.contents.insert(index, item)
        if len(self.contents) > self.tree.order:
            self.shrink(ancestors)

    def remove(self, index, ancestors):
        minimum = self.tree.order // 2

        if self.children:
            # try promoting from the right subtree first,
            # but only if it won't have to resize
            additional_ancestors = [(self, index + 1)]
            descendent = self.children[index + 1]
            while descendent.children:
                additional_ancestors.append((descendent, 0))
                descendent = descendent.children[0]
            if len(descendent.contents) > minimum:
                ancestors.extend(additional_ancestors)
                self.contents[index] = descendent.contents[0]
                descendent.remove(0, ancestors)
                return

            # fall back to the left child
            additional_ancestors = [(self, index)]
            descendent = self.children[index]
            while descendent.children:
                additional_ancestors.append(
                        (descendent, len(descendent.children) - 1))
                descendent = descendent.children[-1]
            ancestors.extend(additional_ancestors)
            self.contents[index] = descendent.contents[-1]
            descendent.remove(len(descendent.children) - 1, ancestors)
        else:
            self.contents.pop(index)
            if len(self.contents) < minimum and ancestors:
                self.grow(ancestors)

class BTree(object):
    BRANCH = LEAF = _BNode

    def __init__(self, order):
        self.order = order
        self._root = self._bottom = self.LEAF(self)

    def _path_to(self, item):
        current = self._root
        ancestry = []

        while getattr(current, "children", None):
            index = bisect.bisect_left(current.contents, item)
            ancestry.append((current, index))
            if index < len(current.contents) \
                    and current.contents[index] == item:
                return ancestry
            current = current.children[index]

        index = bisect.bisect_left(current.contents, item)
        ancestry.append((current, index))
        present = index < len(current.contents)
        present = present and current.contents[index] == item

        return ancestry

    def _present(self, item, ancestors):
        last, index = ancestors[-1]
        return index < len(last.contents) and last.contents[index] == item

    def insert(self, item):
        current = self._root
        ancestors = self._path_to(item)
        node, index = ancestors[-1]
        while getattr(node, "children", None):
            node = node.children[index]
            index = bisect.bisect_left(node.contents, item)
            ancestors.append((node, index))
        node, index = ancestors.pop()
        node.insert(index, item, ancestors)

    def remove(self, item):
        current = self._root
        ancestors = self._path_to(item)

        if self._present(item, ancestors):
            node, index = ancestors.pop()
            node.remove(index, ancestors)
        else:
            raise ValueError("%r not in %s" % (item, self.__class__.__name__))

    def __contains__(self, item):
        return self._present(item, self._path_to(item))

    def __iter__(self):
        def _recurse(node):
            if node.children:
                for child, item in zip(node.children, node.contents):
                    for child_item in _recurse(child):
                        yield child_item
                    yield item
                for child_item in _recurse(node.children[-1]):
                    yield child_item
            else:
                for item in node.contents:
                    yield item

        for item in _recurse(self._root):
            yield item

    def __repr__(self):
        def recurse(node, accum, depth):
            accum.append(("  " * depth) + repr(node))
            for node in getattr(node, "children", []):
                recurse(node, accum, depth + 1)

        accum = []
        recurse(self._root, accum, 0)
        return "\n".join(accum)

    @classmethod
    def bulkload(cls, items, order):
        tree = object.__new__(cls)
        tree.order = order

        leaves = tree._build_bulkloaded_leaves(items)
        tree._build_bulkloaded_branches(leaves)

        return tree

    def _build_bulkloaded_leaves(self, items):
        minimum = self.order // 2
        leaves, seps = [[]], []

        for item in items:
            if len(leaves[-1]) < self.order:
                leaves[-1].append(item)
            else:
                seps.append(item)
                leaves.append([])

        if len(leaves[-1]) < minimum and seps:
            last_two = leaves[-2] + [seps.pop()] + leaves[-1]
            leaves[-2] = last_two[:minimum]
            leaves[-1] = last_two[minimum + 1:]
            seps.append(last_two[minimum])

        return [self.LEAF(self, contents=node) for node in leaves], seps

    def _build_bulkloaded_branches(self, ty):
        leaves, seps = ty
        minimum = self.order // 2
        levels = [leaves]

        while len(seps) > self.order + 1:
            items, nodes, seps = seps, [[]], []

            for item in items:
                if len(nodes[-1]) < self.order:
                    nodes[-1].append(item)
                else:
                    seps.append(item)
                    nodes.append([])

            if len(nodes[-1]) < minimum and seps:
                last_two = nodes[-2] + [seps.pop()] + nodes[-1]
                nodes[-2] = last_two[:minimum]
                nodes[-1] = last_two[minimum + 1:]
                seps.append(last_two[minimum])

            offset = 0
            for i, node in enumerate(nodes):
                children = levels[-1][offset:offset + len(node) + 1]
                nodes[i] = self.BRANCH(self, contents=node, children=children)
                offset += len(node) + 1

            levels.append(nodes)

        self._root = self.BRANCH(self, contents=seps, children=levels[-1])

import random
import unittest


class BTreeTests(unittest.TestCase):
    def test_additions(self):
        bt = BTree(20)
        l = range(2000)
        for i, item in enumerate(l):
            bt.insert(item)
            self.assertEqual(list(bt), l[:i + 1])

    def test_bulkloads(self):
        bt = BTree.bulkload(range(2000), 20)
        self.assertEqual(list(bt), range(2000))

    def test_removals(self):
        bt = BTree(20)
        l = range(2000)
        map(bt.insert, l)
        rand = l[:]
        random.shuffle(rand)
        while l:
            self.assertEqual(list(bt), l)
            rem = rand.pop()
            l.remove(rem)
            bt.remove(rem)
        self.assertEqual(list(bt), l)

    def test_insert_regression(self):
        bt = BTree.bulkload(range(2000), 50)

        for i in range(100000):
            bt.insert(random.randrange(2000))

if __name__ == '__main__':
    #unittest.main()
    b = BTree(4)
    for i in range(0,3):
        b.insert(i)
    print(b)



