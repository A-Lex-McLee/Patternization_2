#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  9 15:29:49 2026

@author: alexanderpfaff
"""

from __future__ import annotations 
from abc import ABC  #, abstractmethod 
from collections.abc import Callable, Iterator 

from Patt_Utils import  _isAtomicConstituent, getLabel, getImmediateChildren   


def _matchLabel(label1: str, label2: str) -> bool: 
    return label1 == label2 or label1.startswith(label2 + "-")  


class Node(ABC): 
    def __init__(self, constituent: str): 
        self._level: int = 0
        self._parent: Node | None = None 
        self._label: str = getLabel(constituent) 
        self._children: list[Node] = []
        self._key: str = ""  
         
    @property 
    def level(self) -> int:
        return self._level 
    
    @property 
    def label(self) -> str:
        return self._label 

    @property 
    def parent(self) -> Node | None:
        return self._parent
        
    @property 
    def key(self) -> str:
        return self._key

    @property 
    def children(self) -> list[Node]: 
        return self._children 
    
        
    def grow(self, constituent) -> None:       
        kids = getImmediateChildren(constituent) 
        if not kids: 
            return                                 
        for index, kid in enumerate(kids, start=1): 
            self._children.append(SyNode(kid, self, child_index=index)) 


    def ancestors(self) ->  Iterator[Node]:
        parent = self.parent
        while parent:
            yield parent
            parent = parent.parent
                
    def descendants(self)  ->  Iterator[Node]:    
        for child in self.children:
            yield child
            yield from child.descendants()       

    def sisters(self) ->  Iterator[Node]: 
        if self.parent is None:
            return        
        for sis in self.parent.children: 
            if sis != self: 
                yield sis
                
    def terminals(self) ->  Iterator[Leaf]: 
        for descendant in self.descendants(): 
            if isinstance(descendant, Leaf): 
                yield descendant 
                
    def terminalCats(self) ->  Iterator[Node]: 
        for descendant in self.descendants(): 
            if ((len(descendant.children) == 1) and 
                isinstance(descendant.children[0], Leaf)): 
                yield descendant 
                
    def terminalLexCats(self) ->  Iterator[Node]: 
        for terminalcat in self.terminalCats(): 
            if terminalcat.children[0].lemma: 
                yield terminalcat  
                                

    
    @property
    def is_preterminal(self) -> bool:
        return (
            len(self.children) > 0
            and all(
                isinstance(child, Leaf)
                for child in self.children
            )
        ) 
    
    
    
    def dominates(self, other: Node) -> bool:
#        return other in self.descendants() 
        return other.key.startswith(self.key + ".")

    def dominates_immediately(self, other: Node) -> bool:
        return other.parent == self 
    
    def dominates_minimally(self, other: Node) -> bool: 
        for intermediate in other.ancestors(): 
            if intermediate == self: 
                return True 
            if _matchLabel(self.label, intermediate.label): 
                return False
        return False

    def c_commands(self, other: Node) -> bool: 
        return any(node in self.sisters() 
                   for node in other.ancestors())


    def precedes(self, other: Node, ancestral_distance: int | None = None) -> bool: 
        return self < other and self._ancestral_distance(other, ancestral_distance)      
        

    def precedes_atMax(self, other: Node, diff: int = 1, ancestral_distance: int | None = None) -> bool:  
        return self < other and abs(self.level - other.level) <= diff and self._ancestral_distance(other, ancestral_distance)       
            

    def precedes_atExactly(self, other: Node, diff: int = 1, ancestral_distance: int | None = None) -> bool: 
        return self < other and abs(self.level - other.level) == diff and self._ancestral_distance(other, ancestral_distance)       


    def _ancestral_distance(self, other: Node, distance: int | None) -> bool: 
         if distance == None: 
             return True 
         source, target = self, other         
         dist_used = 0
         while source.level > target.level: 
             if isinstance(source, Root): 
                 break
             source = source.parent
             dist_used += 1 
         while target.level > source.level:             
             if isinstance(target, Root): 
                 break
             target = target.parent
             dist_used += 1
         while source != target: 
             if isinstance(source, Root) or isinstance(target, Root):
                 break
             source = source.parent
             target = target.parent
             dist_used += 1  
         return source == target and dist_used <= distance     


    def get_minimal_commonAncestor(self, other: Node) -> Node:  
        ancestors = {other, *other.ancestors()} 
        ancestor = self 
        while ancestor is not None and ancestor not in ancestors:   # super-hyper explicit so type checker doesn't complain
#        while ancestor not in ancestors: 
            ancestor = ancestor.parent  
        assert ancestor is not None     # super-hyper explicit 
        return ancestor        
        

    
    
    def walk_X(
            self,
            descend=lambda node, level: True,
            include=lambda node, level: True,
            level=0
            ) -> Iterator[Node]:
    
        for child in self.children:
    
            child_level = level + 1
    
            if include(child, child_level):
                yield child 

            if child.is_preterminal:
                continue                
    
            if descend(child, child_level):
                yield from child.walk(
                    descend,
                    include,
                    child_level
                )



    def _except_cats(self, exceptions: list[str]| None = None): 
        return not any(
            _matchLabel(self.label, exc)
            for exc in exceptions
            )



# 1. go down to terminalLexCats() unless the label is in exceptions = ["PP", "CP"]
# 2. go down 3 levels unless you hit a node in terminalLexCats() before that

# one step further: 
    
# 3. go down to terminalLexCats() unless the label is in exceptions = ["PP", "CP"]; if the label is "PP" extract the head / lemma and append it to the label returned (eg. "PP-með")
    
# 1. 
    # exceptions = ["PP", "CP", "CONJP"]
    # for n in node.walk(
    #     descend=lambda n,l:
    #         not any(
    #             _matchLabel(n.label, exc)
    #             for exc in exceptions
    #         )
    #         ):
    #     print(n.label)



# 2. 
# max_depth = 3 
# for node in np.walk(
#         descend=lambda n,l:
#             l < max_depth
# ):
    




# 3. 
# def node_representation(node):

#     if _matchLabel(node.label, "PP"):

#         head = node.get_head()

#         return f"PP-{head.lemma}"

#     return node.label

# for node in np.walk(...):
#     pattern.append(
#         node_representation(node)
#     )






# def path_to_root(self): 
# def ancestry(self):

# common ancestor
# lowest common ancestor
# domination depth
# structural distance
# government domains
# opacity domains







    
    def walk(
        self,
        include: Callable[[Node, int], bool] = lambda n, l: True,
        descend: Callable[[Node, int], bool] = lambda n, l: True,
        stop: Callable[[Node], bool] = lambda n: n.is_preterminal,
        level: int = 0
    ) -> Iterator[Node]: 
        """
        General-purpose tree traversal ("walker").
        
        ```
        This method recursively traverses the subtree rooted at the current
        node and yields nodes according to user-defined traversal policies.
        
        The walker itself is intentionally linguistically neutral. It knows
        nothing about syntactic categories such as NP, PP, CP, AP, etc.
        Instead, all traversal behaviour is controlled via callback functions.
        
        Conceptually, each encountered node is subjected to three independent
        decisions:
        
            1. include(node, level)
               Should the node be yielded?
        
            2. stop(node)
               Should traversal stop at this node?
        
            3. descend(node, level)
               If traversal has not stopped, should recursion continue into
               the node's children?
        
        This separation makes it possible to express a wide variety of
        traversal strategies without modifying the walker itself.
        
        Parameters
        ----------
        include : Callable[[Node, int], bool], optional
        
            Determines whether a node should be yielded.
        
            The callback receives:
        
                node
                    The currently visited node.
        
                level
                    Depth relative to the node on which walk() was originally
                    invoked.
        
            If include(...) returns True, the node is yielded.
        
            If include(...) returns False, the node is not yielded.
        
            Importantly, returning False does NOT prevent traversal from
            continuing into that node's descendants.
        
            Example
            -------
            Yield only NP nodes:
        
                include=lambda n, l:
                    _matchLabel(n.label, "NP")
        
        
        
        descend : Callable[[Node, int], bool], optional
        
            Determines whether recursion should continue into a node.
        
            The callback receives:
        
                node
                    The currently visited node.
        
                level
                    Depth relative to the starting node.
        
            If descend(...) returns False, the node itself may still be
            yielded (depending on include), but its descendants will not
            be visited.
        
            Example
            -------
            Treat PP and CP as opaque domains:
        
                descend=lambda n, l:
                    not (
                        _matchLabel(n.label, "PP")
                        or
                        _matchLabel(n.label, "CP")
                    )
        
            Result:
        
                NP
                ├── D
                ├── N
                ├── PP
                │   └── ...
                └── CP
                    └── ...
        
            will yield PP and CP themselves, but never enter them.
        
        
        
        stop : Callable[[Node], bool], optional
        
            Absolute stopping condition.
        
            If stop(node) returns True, recursion terminates immediately at
            that node.
        
            Unlike descend(...), this decision takes precedence over all
            further traversal logic.
        
            The default behaviour is:
        
                lambda n: n.is_preterminal
        
            meaning that traversal naturally stops at category nodes such as:
        
                N
                ADJ
                D
                V
                P
        
            without entering their lexical leaves.
        
            This default is particularly useful for syntactic pattern
            extraction, where lexical material is usually irrelevant.
        
            Example
            -------
            Continue all the way down to lexical leaves:
        
                stop=lambda n: False
        
        
        
        level : int, optional
        
            Internal recursion parameter.
        
            Represents the current depth relative to the node on which
            walk() was initially invoked.
        
            Users normally do not specify this argument manually.
        
            The starting node is considered level 0.
        
            Its immediate children are level 1.
        
            Their children are level 2.
        
            And so on.
        
            Example
            -------
            Restrict traversal to three levels:
        
                descend=lambda n, l:
                    l < 3
        
        
        
        Yields
        ------
        Node
        
            Nodes satisfying the traversal policy.
        
            Ordering is depth-first, left-to-right (preorder traversal).
        
        
        
        Notes
        -----
        The walker forms the infrastructural basis for higher-level
        Patternization operations.
        
        Typical workflow:
        
            Tree
                ↓
        
            walk(...)
                ↓
        
            projected sequence
                ↓
        
            pattern matcher
        
        Example:
        
            walk()
                ↓
        
            (D, ADJ, ADJ, N, PP, CP)
        
                ↓
        
            rigid_pattern(...)
            flexi_pattern(...)
            exact_pattern(...)
        
        The walker is responsible only for tree navigation.
        
        Interpretation of the resulting node sequence belongs to later
        processing stages.
        """
    
        for child in self.children:
    
            child_level = level + 1
    
            if include(child, child_level):
                yield child
    
            if stop(child):
                continue
    
            if descend(child, child_level):
                yield from child.walk(
                    include=include,
                    descend=descend,
                    stop=stop,
                    level=child_level
                )





# 1. 
# exceptions = ["PP", "CP", "NP"]

# def descend(node, level):

#     return not any(
#         _matchLabel(node.label, exc)
#         for exc in exceptions
#     )

# pattern = tuple(
#     n.label
#     for n in node.walk(descend=descend)
# )



# 2. 
# max_depth = {
#     "NP": 2,
#     "AP": 1,
#     "CP": 0,
#     "PP": 0
# }
# def descend(node, level):

#     for cat, limit in max_depth.items():

#         if _matchLabel(node.label, cat):
#             return level < limit

#     return True


    
    def exact_pattern(
        pattern: tuple[str, ...],
        query: tuple[str, ...]
    ) -> bool:
    
        return pattern == query


    def rigid_pattern(
        pattern: tuple[str, ...],
        query: tuple[str, ...]
    ) -> bool:
    
        q_len = len(query)
    
        for i in range(
                len(pattern) - q_len + 1):
    
            if pattern[i:i+q_len] == query:
                return True
    
        return False

    
    def flexi_pattern(
        pattern: tuple[str, ...],
        query: tuple[str, ...]
    ) -> bool:
    
        q = 0
    
        for item in pattern:
    
            if item == query[q]:
    
                q += 1
    
                if q == len(query):
                    return True
    
        return False

    
    def left_aligned(
        pattern: tuple[str, ...],
        query: tuple[str, ...]
    ) -> bool:
    
        return pattern[:len(query)] == query
    
    
    
    def right_aligned(
        pattern: tuple[str, ...],
        query: tuple[str, ...]
    ) -> bool:
    
        return pattern[-len(query):] == query


    
    constraints = [
        rigid_pattern,
        left_aligned
    ]


    
    def matches(
        pattern,
        query,
        constraints
    ):
    
        return all(
            constraint(pattern, query)
            for constraint in constraints
        )












    
    def dyck_naked(self) -> str:
        if not self.children:
            return "" # 
        inner = "".join(f"({child.dyck_naked()})" 
                        for child in self.children)
        return inner
    
    
    def dyck_catLabels(self) -> str:
        if not self.children:
            return ""
        child_strings = [
            child.dyck_catLabels()
            for child in self.children
            if child.children #    ignore terminals
        ]
        if child_strings:
            return f"({self.label} {' '.join(child_strings)})"
        else:
            return f"({self.label})"


    def get_terminalSequence(self, output: Callable = lambda n: n.token) -> str: 
        """
        collects information from terminals in order; default setting gives text 
        (modulo punctuation and cliticization); other plausible parameter could be: 
            lambda n: n.lemma (or key??) 

        Parameters
        ----------
        output : Callable, optional
            DESCRIPTION. The default is lambda n: n.token.

        Returns
        -------
        str
            information from the sequence of terminals of self.

        """
        if not self.children:
            return output(self) 
        children_strings = []
        for child in self.children:
            children_strings.append(child.get_terminalSequence(output))        
        return " ".join(children_strings).strip()



    def __str__(self): 
        suffix = "" if len(self.children) == 1 else "s"
        return f" Node[{self._label} with {len(self.children)} child node{suffix}]"

    def __repr__(self): 
        return str(self)

    def __eq__(self, other: Node) -> bool: 
        if not isinstance(other, Node): 
            return NotImplemented 
        return self.key == other.key
        
    def __gt__(self, other: Node) -> bool:  
        if not isinstance(other, Node): 
            return NotImplemented
        if isinstance(self, Root) or isinstance(other, Root): 
            return False 
        if self == other: 
            return False
        s = [int(x) for x in self.key.split('.')] 
        o = [int(x) for x in other.key.split('.')] 
        
        # DOMINANCE: parents don't >>precede<< children
        if len(s) < len(o) and o[:len(s)] == s:
            return False  
        if len(s) > len(o) and s[:len(o)] == o:
            return False  
        comparisons = min(len(s), len(o))  
        for c in range(comparisons): 
            if s[c] > o[c]: 
                return True 
            if s[c] < o[c]: 
                return False 
        return False

    def __lt__(self, other: Node) -> bool:  
        if not isinstance(other, Node): 
            return NotImplemented
        if isinstance(self, Root) or isinstance(other, Root): 
            return False   
        s = self.key.split('.')
        o = other.key.split('.')
        if (len(s) < len(o) and o[:len(s)] == s) or (len(s) > len(o) and s[:len(o)] == o):
            return False
        return not (self == other) and not (self > other) 
    
    def __hash__(self) -> str:
        return hash(self.key)



class Root(Node): 
    def __init__(self, constituent: str): 
        super().__init__(constituent) 
        self._key = "ROOT"
        self._level: int = 0
        
        self.grow(constituent)

    def __str__(self):
        return f"ROOT ->{super().__str__()}"


class SyNode(Node): 
    def __init__(self, constituent: str, parent: Node, child_index: int) -> None:  
        super().__init__(constituent)
        self._level: int = parent.level + 1  
        self._parent: Node = parent 

        if parent.key == "ROOT":
            self._key = str(child_index)
        else:
            self._key = f"{parent.key}.{child_index}"        
        
        
        if _isAtomicConstituent(constituent):  
            self._children.append(Leaf(constituent, self, child_index=1))
            return  
        else: 
            self.grow(constituent)

    def __str__(self):
        return f"Non-terminal ->{super().__str__()}"

        
class Leaf(Node): 
    def __init__(self, constituent, parent: Node, child_index: int): 
        super().__init__(constituent)
    
        self._level = parent.level + 1
        self._parent = parent
        self._key = f"{parent.key}.{child_index}"
        
        self._lemma = "" 
        self._token = ""
        self._null = "" 
        self._index = ""

        start = constituent.find(" ")  
        label = constituent[start:-1].strip()  
        label = label.split('-') 
        if len(label) == 2: 
            if not "*" in label[0]: 
                self._token, self._lemma = label 
                # self._token = self._token.removeprefix('$').removesuffix('$') 
                self._label = f">>> [{self._lemma}: {self._token}]"
            else: 
                self._null = label[0] 
                self._index = label[1]
                self._label = f">>> [{self._null}-{self._index}]"  
                
        elif constituent[-2].isdigit(): 
            self._index = int(constituent[-2])  
            self._null = constituent[1:-2].strip()
            self._label = f">>> [{self._null}-{self._index}]"  
        else: 
            self._label = f">>> {label}"  
            if not "*" in label[0]: 
                self._token = label[0] 
                self._lemma = label[0] 
            else: 
                self._null = label[0]

        self._children =  []   
        
    
    def __str__(self):
        return f"terminal -> Node( {self.label} )"
    
    @property 
    def lemma(self): 
        return self._lemma 
    
    @property 
    def token(self): 
        return self._token 
    
    @property 
    def null(self): 
        return self._null 
    
    @property 
    def index(self): 
        return self._index 
    
    
    
class Tree:
    def __init__(self, root_node: Root, ID: str = "unknown", text_ID: str = "UNknown"):
        self._root = root_node 
        self._id = ID 
        self._text_id = text_ID
        self.source: str = ""
        self.target: str = ""
        self.tree_rel: str = ""
        

    @property 
    def root(self) -> Node: 
        return self._root 
    
    @property 
    def ID(self) -> str: 
        return self._id      
    
    @property 
    def text_ID(self) -> str: 
        return self._text_id      
    
    def __eq__(self, other: Tree) -> bool: 
        if not isinstance(other, Tree): 
            return NotImplemented  
        return self.root == other.root and self.source == other.source ##   
        
    

    def __str__(self) -> str:
        """Approximates the tree layout using visual text markers."""
        return self._render_tree_ascii(self.root)

    def _render_tree_ascii(self, node: Node, prefix: str = "", is_last: bool = True) -> str:
        # Choose the right branch character based on structural positioning
        marker = "└── " if is_last else "├── "
        
        # Render the current line
        result = f"{prefix}{marker}{node.label} (Key: {node.key})\n"
        
        # Adjust the indentation indentation for sub-children
        new_prefix = prefix + ("    " if is_last else "│   ")
        
        # Recursively assemble child text layouts
        child_count = len(node.children)
        for i, child in enumerate(node.children):
            child_is_last = (i == child_count - 1)
            result += self._render_tree_ascii(child, new_prefix, child_is_last)
            
        return result 
    

    def find_nodes(self, criterion: Callable[[Node], bool], 
                     current_node: Node | None = None) -> list[Node]:
        """ 
        traverses the tree and returns a list of all nodes that satisfy the criterion.
        'criterion' is a functional parameter (lambda or function that returns bool).
        """
        if current_node is None:
            current_node = self.root

        hits = []
        
        if criterion(current_node):
            hits.append(current_node)
            
        for child in current_node.children:
            hits.extend(self.find_nodes(criterion, child))
            
        return hits 
    

    def find_node(self, criterion: Callable[[Node], bool], 
                  current_node: Node | None = None) -> Node | None:
        """ 
        returns the first node that satisfies the criterion; 
        use for key or existential query (is there ...)
        """
        if current_node is None:
            current_node = self.root

        if criterion(current_node):
            return current_node
            
        for child in current_node.children:
            result = self.find_node(criterion, child)
            if result is not None:
                return result
                
        return None 
    
    
                
    def _collect_nodePairs(self, source: str, target: str
                           ) -> tuple[list[Node], list[Node]]:
        
        criterion_source = lambda n: _matchLabel(n.label, source) 
        criterion_target = lambda n: _matchLabel(n.label, target) 
        
        source_nodes = self.find_nodes(criterion_source) 
        target_nodes = self.find_nodes(criterion_target) 
        
        return source_nodes, target_nodes
  
    

    def dominates_cat(self, source: str, target: str,
                      dom_criterion: Callable[[Node, Node], bool] = lambda n1, n2: True
                      ) -> list[tuple[Node, Node]]: 
        criterion_source = lambda n: _matchLabel(n.label, source)  
        source_nodes = self.find_nodes(criterion_source) 
        matches: list[tuple[Node, Node]] = []
        for dom in source_nodes: 
            for tar in dom.descendants(): 
                if dom_criterion(dom, tar) and _matchLabel(tar.label, target): 
                    matches.append((dom, tar))                     
        return matches 
        

    def dominates_lemma(self, source: str, target: str) -> list[tuple[Node, Node]]:  
        criterion_source = lambda n: _matchLabel(n.label, source)  
        source_nodes = self.find_nodes(criterion_source) 
        matches: list[tuple[Node, Node]] = []
        for dom in source_nodes: 
            for tar in dom.terminals(): 
                if tar.lemma == target: 
                    matches.append((dom, tar))                     
        return matches 
    


    def c_commands(self, source_cat: str, target_cat: str) -> list[tuple[Node, Node]]: 
        
        commandores, targets = self._collect_nodePairs(source_cat, target_cat) 
        matches: list[tuple[Node, Node]] = [] 
        for com in commandores: 
            if isinstance(com, Root):
                continue 
            for tar in targets: 
                if tar.level <= com.level: 
                    continue 
                if com.c_commands(tar): 
                        matches.append((com, tar)) 
        return matches
        


        
    def precedes(self, source_cat: str, target_cat: str, 
                 ancestral_distance: int | None = None) -> list[tuple[Node, Node]]: 
        precats, postcats = self._collect_nodePairs(source_cat, target_cat) 
        return [(pre, post) for pre in precats for post in postcats 
#                if pre < post and self._ancestral_distance(pre, post, ancestral_distance)]
                if pre.precedes(post, ancestral_distance)]






    def precedes_atMax(self, source_cat: str, target_cat: str, diff: int = 1,
                       ancestral_distance: int | None = None) -> list[tuple[Node, Node]]: 
        precats, postcats = self._collect_nodePairs(source_cat, target_cat) 
        return [(pre, post) for pre in precats for post in postcats 
                if pre.precedes_atMax(post, diff, ancestral_distance)]



    def precedes_atExactly(self, source_cat: str, target_cat: str, diff: int = 1,
                           ancestral_distance: int | None = None) -> list[tuple[Node, Node]]: 
        precats, postcats = self._collect_nodePairs(source_cat, target_cat) 
        
        return [(pre, post) for pre in precats for post in postcats 
                if pre.precedes_atExactly(post, diff, ancestral_distance)]
    
    
    
    # def _ancestral_distance(self, source_node: Node, target_node: Node, distance: int | None) -> bool: 
    #     if distance == None: 
    #         return True 
    #     source, target = source_node, target_node         
    #     dist_used = 0
    #     while source.level > target.level: 
    #         if isinstance(source, Root): 
    #             break
    #         source = source.parent
    #         dist_used += 1 
                        
    #     while target.level > source.level:             
    #         if isinstance(target, Root): 
    #             break
    #         target = target.parent
    #         dist_used += 1
                    
    #     while source != target: 
    #         if isinstance(source, Root) or isinstance(target, Root):
    #             break
    #         source = source.parent
    #         target = target.parent
    #         dist_used += 1  
        
    #     return source == target and dist_used <= distance 
    
            

    # def get_minimal_commonAncestor(
    #         self,
    #         node1: Node,
    #         node2: Node
    #         ) -> Node:
    
    #     ancestors2 = {node2, *node2.ancestors()}
    
    #     ancestor = node1
    
    #     while ancestor not in ancestors2:
    #         ancestor = ancestor.parent
    
    #     return ancestor




class SearchForest: 
    def __init__(self, data: dict[dict[str, str]] | None, from_fully_spec_trees: bool = False) -> None: 
        self._forest: list[Tree] = []
        if not from_fully_spec_trees: 
            
            self._forest = [
                Tree(Root(parsed_constituent), unit_id, text_id)
                for text_id, units in data.items()
                for unit_id, parsed_constituent in units.items()
                if parsed_constituent 
                if parsed_constituent.count("(") == parsed_constituent.count(")")
            ]            
            
    @property 
    def forest(self) -> list[Tree]: 
        return self._forest  
    
    @property 
    def size(self) -> int: 
        return len(self.forest)
    
    
    @classmethod 
    def from_trees(cls, trees: list[Tree]) -> None: 
        skogr = SearchForest(None, from_fully_spec_trees=True)
        skogr._forest = trees[:]
        return skogr
    

    def root_dominates_cat(self, target: str, ID_only: bool = False) -> dict[str, list[tuple(Node,Node)]] | list[str]:   
        """
        = contains 

        Parameters
        ----------
        catlabel : str
            DESCRIPTION.

        Returns
        -------
        None.

        """
        matches: dict = dict() 
        for tree in self.forest: 
            hits = [pair 
                   for pair in tree.dominates_cat(tree.root.label, target) 
                   if isinstance(pair[0], Root)] 
            if hits: 
                matches[tree.ID] = hits  
        if ID_only: 
            return matches.keys()
        else:
            return matches
            


    def root_dominates_lemma(self, target: str, ID_only: bool = False) -> dict[str, list[tuple(Node,Node)]] | list[str]: 
        """
        = contains 

        Parameters
        ----------
        catlabel : str
            DESCRIPTION.

        Returns
        -------
        None.

        """
        matches: dict = dict() 
        for tree in self.forest: 
            hits = [pair 
                   for pair in tree.dominates_lemma(tree.root.label, target) 
                   if isinstance(pair[0], Root)] 
            if hits: 
                matches[tree.ID] = hits  
        if ID_only: 
            return matches.keys()
        else:
            return matches
      
    def cat_dominates_cat(self, source: str, target: str, ID_only: bool = False) -> dict[str, list[tuple(Node,Node)]] | list[str]:
        matches: dict = dict()
        for tree in self.forest: 
            hits = tree.dominates_cat(source, target, dom_criterion = lambda n1, n2: n1.dominates(n2)) 
            if hits: 
                matches[tree.ID] = hits 
        if ID_only: 
            return matches.keys()
        else:
            return matches
      
    def cat_immediately_dominates_cat(self, source: str, target: str, ID_only: bool = False) -> dict[str, list[tuple(Node,Node)]] | list[str]:
        matches: dict = dict()
        for tree in self.forest: 
            hits = tree.dominates_cat(source, target, dom_criterion = lambda n1, n2: n1.dominates_immediately(n2)) 
            if hits: 
                matches[tree.ID] = hits 
        if ID_only: 
            return matches.keys()
        else:
            return matches
            
    def cat_minimally_dominates_cat(self, source: str, target: str, ID_only: bool = False) -> dict[str, list[tuple(Node,Node)]] | list[str]:
        matches: dict = dict()
        for tree in self.forest: 
            hits = tree.dominates_cat(source, target, dom_criterion = lambda n1, n2: n1.dominates_minimally(n2)) 
            if hits: 
                matches[tree.ID] = hits 
        if ID_only: 
            return matches.keys()
        else:
            return matches
    
    
    def cat_dominates_lemma(self, source: str, target: str, ID_only: bool = False) -> dict[str, list[tuple(Node,Node)]] | list[str]:
        matches: dict = dict()
        for tree in self.forest:              
            hits = [pair 
                   for pair in tree.dominates_lemma(source, target)] 
            if hits: 
                matches[tree.ID] = hits 
        if ID_only: 
            return matches.keys()
        else:
            return matches
            

    def cat_c_commands_cat(self, source: str, target: str, ID_only: bool = False) -> dict[str, list[tuple(Node,Node)]] | list[str]:

        matches: dict = dict()
        for tree in self.forest:
            hits = [pair 
                   for pair in tree.c_commands(source, target)] 
            if hits: 
                matches[tree.ID] = hits 
        if ID_only: 
            return list(matches.keys())
        else:
            return matches
            

    
    
    def precedes(self, source: str, target: str, 
                 ancestral_distance = None, ID_only: bool = False
                 ) -> dict[str, list[tuple(Node,Node)]] | list[str]:
        
        matches: dict = dict()
        for tree in self.forest:   
            hits = [pair 
                   for pair in tree.precedes(source, target, 
                                             ancestral_distance=ancestral_distance)] 
            if hits: 
                matches[tree.ID] = hits 
        if ID_only: 
            return list(matches.keys())
        else:
            return matches
            
            
    
    def precedes_atMax(self, source: str, target: str, diff: int = 1, 
                           ancestral_distance = None, ID_only: bool = False 
                           ) -> dict[str, list[tuple(Node,Node)]] | list[str]:
        
        matches: dict = dict()
        for tree in self.forest:   
            hits = [pair 
                   for pair in tree.precedes_atMax(source, target, diff=diff, 
                                                   ancestral_distance=ancestral_distance)] 
            if hits: 
                matches[tree.ID] = hits 
        if ID_only: 
            return list(matches.keys())
        else:
            return matches
            
            
    
    def precedes_atExactly(self, source: str, target: str, diff: int = 1, 
                           ancestral_distance = None, ID_only: bool = False 
                           ) -> dict[str, list[tuple(Node,Node)]] | list[str]:
        
        matches: dict = dict()
        for tree in self.forest:   
            hits = [pair 
                   for pair in tree.precedes_atExactly(source, target, diff=diff, 
                                             ancestral_distance=ancestral_distance)] 
            if hits: 
                matches[tree.ID] = hits 
        if ID_only: 
            return list(matches.keys())
        else:
            return matches
            
            
            
            
    
    
    
    def individualizeHits(self, matches: list) -> list[tuple[str, Node, Node]]: 
        flatMatches = []
        for key, val in matches.items(): 
            for node_pair in val: 
                match = (key, ) + node_pair 
                flatMatches.append(match)
        return flatMatches
        




    
    
    
    
    def find_by_key(self, key: str, current_node: Node | None = None) -> Node | None:
        """Navigates and fetches any node instantly via its hierarchical path key."""
        if current_node == None:
            current_node = self.root
            
        if current_node.key == key:
            return current_node
            
        for child in current_node.children:
            result = self.find_by_key(key, child)
            if result:
                return result
        return None
    
    
                
        

    # def dyck(self) -> str:
    #     if not self.children:
    #         return "" # or self.label  
    #     children_strings = []
    #     for child in self.children:
    #         children_strings.append(f"({child.dyck()})")        
    #     return "".join(children_strings)
             
        
