#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 29 20:38:43 2026

@author: alexanderpfaff
"""


import re
import sqlite3
from collections.abc import Sequence


def get_bracket_span(txt: str, 
                     start_idx: int = 0, 
                     open_bracket: str = '(',
                     close_bracket: str = ')'
                     ) -> tuple[int, int]:

    idx = txt.find(open_bracket, start_idx)
    if idx == -1:
        raise ValueError("No opening bracket found")
    start = idx
    depth = 0
    length = len(txt)
    while idx < length:
        ch = txt[idx]
        if ch == open_bracket:
            depth += 1
        elif ch == close_bracket:
            depth -= 1
            if depth == 0:
                return start, idx + 1 
        if depth < 0:
            raise ValueError("Improper bracketing") 
        idx += 1
    raise ValueError("Unbalanced brackets") 
    
    
    
def get_backbracket_span(txt: str, 
                         start_idx: int, 
                         open_bracket: str = '(',
                         close_bracket: str = ')'                         
                         ) -> int: 
    
    """ use only if you have idx position for closing bracket!  """ 
    
    if txt[start_idx] != close_bracket:
        raise ValueError("No closing bracket at start_idx")
    depth = 0
    idx = start_idx
    while idx >= 0:
        ch = txt[idx]
        if ch == close_bracket:
            depth += 1
        elif ch == open_bracket:
            depth -= 1

            if depth == 0:
                return idx
        idx -= 1    
    raise ValueError("Unbalanced brackets")    




def findCat(txt: str, cat: str) -> list[tuple[int, int]]:
    myRegex = r'\((\S+)'
    return [get_bracket_span(txt, m.start()) 
            for m in re.finditer(myRegex, txt)
            if m.group(1) == cat]


def findSubCat(txt: str, cat: str) -> list[tuple[int, int]]:
    myRegex = r'\((\S+)'
    return [get_bracket_span(txt, m.start())
            for m in re.finditer(myRegex, txt)
            if m.group(1) == cat
            or m.group(1).startswith(cat + "-") ]


def findLemma(txt: str, lemma: str) -> list[tuple[int, int]]:
    myRegex =  r'([^\s()]+)-([^\s()]+)\)'
    return [(get_backbracket_span(txt, m.end()-1), m.end())  
            for m in re.finditer(myRegex, txt)
            if m.group(2) == lemma]


def getLabel(constituent: str) -> str:
    if not constituent.startswith("("): 
        
        print(f"======  {constituent}  ==============")
        
        raise ValueError("Not a constituent")
    end = constituent.find(" ")
    if end == -1:
        raise ValueError("No label found")
    return constituent[1:end]


def label_level(label: str, level: int = 1) -> str:
    return "-".join(label.split("-")[:level])


def extractLabels(constituents: Sequence[str,...], level: int = None) -> set[str]:
    regex_str = r'\((\S+)'
    return {
        label_level(m.group(1), level)
        for n in constituents
        for m in re.finditer(regex_str, n)
    }


def _isAtomicConstituent(constituent: str) -> bool:
    """
    precondition: only proper constituents = strings that start/end with "(" / ")" are legal arguments 
    therefore, we use a simple string method and don't check position
    """
    return (constituent.count('(') == constituent.count(')') == 1)  
    

def _isAbstractLeaf(constituent: str) -> bool: 
    return _isAtomicConstituent(constituent) and constituent.count("*") >= 2




def getImmediateChildrenIdx(constituent: str) -> list[tuple[int,int]]: 
    """
    parses a constituent string "(XP A B C )" and returns start and end indices (+1) f
    for all immediate children (i.e. depth 1, here: A, B C)

    Parameters
    ----------
    constituent : str
        properly bracketed constituent string.

    Returns
    -------
    list[tuple[int,int]]
        slicing indices indicating start and end positions of immediate children.

    """
    childrenIdx: list[str] = []
    idx = constituent.find(" ") 
    while True:
        idx = constituent.find("(", idx)
        if idx == -1:
            break
        start, end = get_bracket_span(constituent, idx)
        childrenIdx.append((start, end))
        idx = end
    return childrenIdx


def getImmediateChildren(constituent):
    return [
        constituent[start:end]
        for start, end in getImmediateChildrenIdx(constituent)
    ]


def getDescendantsAtDepthIdx(constituent: str, depth: int = 2) -> list[tuple[int,int]]: 
    d_children = []  
    def descend(node: str, level: int, offset: int):  
        if level == depth or _isAtomicConstituent(node): 
            d_children.append((offset, offset + len(node))) 
            return 
        for start, end in getImmediateChildrenIdx(node):
            global_start = offset + start
            child = node[start:end]
            descend(
                child,
                level + 1,
                global_start
            )            
    descend(constituent, level = 0, offset = 0) 
    return d_children

def getDescendantsAtDepth(constituent: str, depth: int = 2):
    descendants = []
    def descend(node: str, level: int):
        if level == depth or _isAtomicConstituent(node):
            descendants.append(node)
            return
        for start, end in getImmediateChildrenIdx(node):
            descend(node[start:end], level + 1)
    descend(constituent, 0)
    return descendants
    



# to do
def getDescendantsUpToDepthIdx(constituent: str, depth: int = 2) -> list[tuple[int,int]]: 
    d_children = []  
    def descend(node: str, level: int, offset: int):  
        if level == depth or _isAtomicConstituent(node): 
            d_children.append((offset, offset + len(node))) 
            return 
        for start, end in getImmediateChildrenIdx(node):
            global_start = offset + start
            child = node[start:end]
            descend(
                child,
                level + 1,
                global_start
            )            
    descend(constituent, level = 0, offset = 0) 
    return d_children









def getLabels_preorder(constituent, max_depth):
    tokens = re.findall(r'\(\s*[^\s()]+|\)', constituent)
    labels = []
    current_depth = 0
    for token in tokens:
        if token == ')':
            current_depth -= 1
        else:
            current_depth += 1
            if current_depth <= max_depth:
                label = token.lstrip('(').strip()
                labels.append(label)
    return labels





def get_labels_breadth_first(constituent, max_depth):
    tokens = re.findall(r'\(\s*[^\s()]+|\)', constituent)
    levels = [[] for _ in range(max_depth)]
    current_depth = 0
    for token in tokens:
        if token == ')':
            current_depth -= 1
        else:
            current_depth += 1
            if current_depth <= max_depth:
                label = token.lstrip('(').strip()

                levels[current_depth - 1].append(label)
                
    flat_labels = []
    for lvl in levels:
        flat_labels.extend(lvl)
        
    return flat_labels


  
            
            
            

def get_dominationPaths(constituent: str, cat: str, 
                        matchRelation: callable = lambda x, y: x == y
                        ) -> list[str, ...]:
    tokens = re.finditer(r'\(\s*[^\s()]+|\)', constituent)

    all_paths = []
    current_path = []  
    for token in tokens:
        if token.group().startswith('('):
            label = token.group().lstrip('(').strip()
            current_path.append(label) 
                        
            if matchRelation(cat, label):  
                
                idxx = get_bracket_span(constituent, start_idx=token.start())
                
                current_path.append(idxx) 

                all_paths.append(current_path[:]) 
                current_path.pop()

        elif token == ')':
            if current_path:
                current_path.pop()
            
    return all_paths
            
            
            









def getImmediatePattern(constituent: str): 
    cats: list[str] = []
    idx = constituent.find(" ") 
    while True:
        idx = constituent.find("(", idx)
        if idx == -1:
            break
        start, end = get_bracket_span(constituent, idx)
        label = getLabel(constituent[start:end])
        cats.append(label)
        idx = end
    return tuple(cats), getLabel(constituent)





def getPatterns(subcat: str, constituents: Sequence[str]) :
    
    patterns = [] 
    
    # NB: c is the ID of the constituent! 
    for c in constituents: 
        
        cat_indices = findSubCat(c, subcat)  
        
        for start, end in cat_indices: 
            
            patt = getImmediatePattern(c[start:end]) 
#            patt = getMediatePatterns(constituents[c][start:end]) 
            
            patterns.append(patt) 
        
    return patterns    
    



# db access

def getParsedText(db_path: str) -> list[str]: 
    
    conn = sqlite3.connect(db_path) 
    try:
        cur = conn.cursor()
        row = cur.execute("""
            SELECT schema_name, schema_version
            FROM database_info
        """).fetchone()
        if row != ("TextToDB", "2.0"):
            raise ValueError("Not a valid TextToDB v2.0 database")
    
        cur.execute("""
            SELECT parsed_text
            FROM units
        """)
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()
    



def getParsedTextWithID(db_path) -> dict[str, str]:

    conn = sqlite3.connect(db_path) 
    try:
        cur = conn.cursor()
        row = cur.execute("""
            SELECT schema_name, schema_version
            FROM database_info
        """).fetchone()
        
        if row != ("TextToDB", "2.0"):
            raise ValueError("Not a valid TextToDB v2.0 database")
    
        cur.execute("""
            SELECT unit_id, parsed_text
            FROM units
        """)
        rows = cur.fetchall()
        
        return {unit_id: parsed_text
                for unit_id, parsed_text in rows}
    finally:
        conn.close()
    




def getParsedTextWithIDs(db_path) -> dict[str, str]:

    conn = sqlite3.connect(db_path) 
    try:
        cur = conn.cursor()
        row = cur.execute("""
            SELECT schema_name, schema_version
            FROM database_info
        """).fetchone()
        
        if row != ("TextToDB", "2.0"):
            raise ValueError("Not a valid TextToDB v2.0 database")
    
        
        cur.execute("""
            SELECT
                tu.text_id,
                u.unit_id,
                u.parsed_text
            FROM units u
            JOIN text_units tu
                ON u.unit_id = tu.unit_id
            ORDER BY tu.text_id, u.unit_id
        """)

        
        out = {}
        
        for text_id, unit_id, parsed_text in cur.fetchall():
        
            if text_id not in out:
                out[text_id] = {}
        
            out[text_id][unit_id] = parsed_text
        
        return out

    finally:
        conn.close()
    










# VBPI^3^SG 



# NP-POS-3, IP-SUB-3, CP-THT-PRN-2, 


# IP-MAT-SPE=2











# # @aux function
# def _get_cursor(db_path: str):

#     conn = sqlite3.connect(db_path)

#     cur = conn.cursor()

#     row = cur.execute("""
#         SELECT schema_name, schema_version
#         FROM database_info
#     """).fetchone()

#     if row != ("TextToDB", "1.0"):
#         conn.close()
#         raise ValueError(
#             "Not a valid TextToDB v1.0 database"
#         )

#     return conn, cur






# def extractLabels(
#         constituents: Sequence[str],
#         regex_str: str
#         ) -> set[str]:

#     return {
#         m.group(1)
#         for n in constituents
#         for m in re.finditer(regex_str, n)
#     }


# fullLabels = extractLabels(
#     constituents,
#     r'\((\S+)'
# )

# mainCats = extractLabels(
#     constituents,
#     r'\(([A-Z]+)'
# )






