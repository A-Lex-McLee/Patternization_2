#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 20:26:29 2026

@author: alexanderpfaff
"""

import re
import sqlite3
from collections import defaultdict

from Patt_Utils import get_bracket_span, findCat


t1 = "psd/1150.firstgrammar.sci-lin.psd"  
t2 = "psd/1250.sturlunga.nar-sag.psd"
t3 = "Histories1.psd"
t4 = "Histories2.psd"
t5 = "Histories3.psd"
t6 = "Mark.psd"
t7 = "Matthew.psd"
t8 = "heliand.psd" 
t9 = "wikipedia_KYOTO_9.psd"  
t10 = "psd/1475.aevintyri.nar-rel.psd"



class TextToDB: 
    
    def __init__(self, source_txt: str | None = None, db_name: str | None = None) -> None: 
        self._open_bracket: str = '(' 
        self._close_bracket: str = ')'
        self._undesirables: list[str] = ['CODE', 'VERSION', '.', ',', "'"]        
        self._lemma_tokens: dict[str, str] = defaultdict(list[str])

        if source_txt and db_name:
            self.initialize_textToDB(source_txt, db_name)



        
    def _removePrologue(self, txt: str) -> str:
        """
        Remove corpus-specific header material
        preceding the first top-level Penn unit.
        """
        m = re.search(r'\(\s*\([A-Z]', txt)
        if m is None:
            raise ValueError("No corpus start found")
        return txt[m.start():]
    

    def add_undesirables(self, *cats) -> None: 
        self._undesirables.extend(cats) 
        
        
    def _pruneUndesirables(self, txt: str):
        spans = []
        for cat in self._undesirables:
            spans.extend(findCat(txt, cat)) 
        out = self._cut_spans(txt, spans)
        return ' '.join(out.split())

    
    def _cut_spans(self, txt: str, spans: list[tuple[int, int]]) -> str:
        out = []
        current = 0
        for start, end in sorted(spans):
            out.append(txt[current:start])
            current = end
        out.append(txt[current:])
        return ''.join(out)
    
    def cutCat(self, txt: str, cat: str) -> str:
        return self._cut_spans(txt, findCat(txt, cat))


    def _removeEmptyBrackets(self, txt: str) -> str:
        spans = []
        ix = txt.find(self._open_bracket)
        while ix != -1:
            start, end = get_bracket_span(txt, ix, self._open_bracket, self._close_bracket) 
            if txt[start + 1:end - 1].strip() == "":
                spans.append((start, end))
            ix = txt.find(self._open_bracket, end)
        return self._cut_spans(txt, spans)
    

    
    def _isWrapper(self, txt: str, start: int, end: int) -> bool:
        inside = txt[start+1:end-1]
        pos = 0
        while pos < len(inside) and inside[pos].isspace():
            pos += 1
        if pos == len(inside):
            return False
        if inside[pos] != self._open_bracket:
            return False
        child_start, child_end = get_bracket_span(inside, pos, self._open_bracket, self._close_bracket)
        return inside[child_end:].strip() == ""

    
    def _removeWrapper(self, txt: str) -> str:
        spans = []
        ix = txt.find(self._open_bracket)
        while ix != -1:
            start, end = get_bracket_span(txt, ix, self._open_bracket, self._close_bracket)
            if self._isWrapper(txt, start, end):
                spans.append((start, start+1))      # remove outer (
                spans.append((end-1, end))          # remove outer )
            ix = txt.find(self._open_bracket, end)
        return self._cut_spans(txt, spans)
    
        

    
    def _merge_dollar_tokens(self, tokens: list[str]) -> list[str]:
        out = []
        i = 0
        while i < len(tokens):
            if (
                tokens[i].endswith("$")
                and i + 1 < len(tokens)
                and tokens[i + 1].startswith("$")
            ):
                out.append(
                    tokens[i][:-1] + tokens[i + 1][1:]
                )
                i += 2
            else:
                out.append(tokens[i])
                i += 1
        return out 


    def goLexical(self, txt: str) -> tuple[str, tuple[str, ...]]: 
        myRegex =  r'([^\s()]+)-([^\s()]+)\)' 
        lex_pairs = [(m.group(1), m.group(2)) 
                     for m in re.finditer(myRegex, txt)
                     if "*" not in m.group(1)] 
        
        if not lex_pairs:
            return "", []

        tokens, lemmata = zip(*lex_pairs)

        self._update_lemma_token_correspondences(lex_pairs)
        text = self._getText(tokens) 
        
        return text, lemmata


    def _update_lemma_token_correspondences(self, lex_pairs: list[tuple[str, str]]) -> None:         
        for token, lemma in lex_pairs: 
            token = token.removeprefix('$').removesuffix('$') 
            self._lemma_tokens[lemma].append(token)
        

    def _getText(self, tokens: list[str]) -> str: 
        mergedTokens = self._merge_dollar_tokens(tokens)
        return " ".join(mergedTokens)


    
    def _getUnits(self, txt: str) -> list[tuple[int, int]]: 
        indices = []
        start, end  = 0, 0  
        while txt.find(self._open_bracket, end) != -1:
            start, end = get_bracket_span(txt, start_idx=end, 
                                          open_bracket=self._open_bracket, 
                                          close_bracket=self._close_bracket)  
            
            indices.append((start, end)) 
        return indices
        
    
    def _chopUnit(self, txt: str, start: int, end: int) -> list[str]: 
        unit = txt[start:end]
        done = False
        out = [] 
        start_idx = 1
        while not done: 
            start, end = get_bracket_span(unit, start_idx=start_idx,  
                                          open_bracket=self._open_bracket, 
                                          close_bracket=self._close_bracket)
            out.append(unit[start:end]) 
            start_idx = end + 1
            if unit.find(self._open_bracket, start_idx) == -1:
                done = True
        return out




    
    def getConstituents_andText(self, txt: str) -> dict[str, dict]: 
        """
        Extract constituent data and update lemma-token correspondences.
        """
        units = self._getUnits(txt) 
        ref_counter = 0
        out = dict()
        for start, end in units: 
            unit = self._chopUnit(txt, start, end)
    
            if len(unit) < 2: 
                reference = f"unknown_{str(ref_counter)}"  
                ref_counter += 1
            else:
                reference = unit[1]        
                id_start = reference.find(" ") + 1
                id_end = reference.find(")")
                reference = reference[id_start:id_end]
            
            constituent = "(nada)" if len(unit) < 1 else unit[0]   
            
            text, lemmata = self.goLexical(constituent)  
            
            constituent = self._pruneUndesirables(constituent) 
            constituent = self._removeEmptyBrackets(constituent)
            
            out[reference] = {
                "parsed_constituent": constituent,
                "surface_text": text, 
                "lemmata": lemmata
                }
        return out 



    # lousy!!! TODO!!!!
    def _extract_text_name(self, text_id: str) -> str: 
        # import re
        # # Hvert snið er skilgreint nákvæmlega eins og það á að mætast:
        # # 1. (?:^\d+_)?([^;]+) -> Grípur allt eftir "3_" og fram að ";" (Wikipedia)
        # # 2. ([^:]+)(?=: )     -> Grípur allt fram að ":" (Herodotus)
        # # 3. (.*?,[^,]+)(?=,\d) -> Grípur allt fram að seinustu kommu sem fylgdi tala (Sturlunga)
        # # 4. ([^\.]+)(?=\.)     -> Grípur allt fram að fyrsta punktinum (OSHeliand)
    
        # pattern = r"(?:^\d+_)?([^;]+);|(.*?)(?=:)|(.*?)(?=,\d)|([^\.]+)(?=\.)"
    
        # match = re.search(pattern, text_id)
        # if match:
        #     # Finnum þann hóp úr regexinu sem fann samsvörun (sleppum None gildum)
        #     core = next((g for g in match.groups() if g is not None), text_id)
        #     return core.strip()
    
        # return text_id 
        # 1. Herodotus: Skerum sérstaklega af við fyrsta tvípunktinn (:)
        if text_id.startswith("Herodotus") or text_id.startswith("Greek"):
            return text_id.split(":")[0].strip()
    
        # 2. Wikipedia: Sleppir upphafsstafnum (t.d. "3_") og grípur allt að fyrsta ";"
        if text_id.startswith(("0_", "1_", "2_", "3_", "4_", "5_", "6_", "7_", "8_", "9_")) and ";" in text_id:
            match = re.match(r"(?:^\d+_)?([^;]+)", text_id)
            if match: 
                return match.group(1).strip()
    
        # 3. IcePaHC (Sturlunga, Ævintýri o.fl.): Skerum einfaldlega af við FYRSTU kommu (,)
        # Þar sem við erum þegar búin að grípa Herodotus hér að ofan, þá virkar þetta fullkomlega
        if "," in text_id:
            return text_id.split(",")[0].strip()
    
        # 4. OSHeliand: Skerum af við fyrsta punktinn (.)
        if "." in text_id:
            return text_id.split(".")[0].strip()
            
        return text_id.strip()




    
    #####################
    # ==========================================================
    # initialization
    # ==========================================================
    
    def initialize_textToDB(
            self,
            source_txt: str,
            db_name: str 
#            text_id: str
            ) -> None:
        """
        Read a corpus file, preprocess it, extract units,
        and build the SQLite database.
        """
        with open(source_txt, "r", encoding="utf-8") as f:
            txt_str = f.read()
    
        txt = " ".join(txt_str.split())
        txt = self._removePrologue(txt) 
        
        # txt = self._removeWrapper(txt)
        txt = self._removeEmptyBrackets(txt)
    
        constituents = self.getConstituents_andText(txt) 
        
        for label in constituents.keys(): 
            if "unknown" in label: 
                continue 
            text_id = self._extract_text_name(label) 
            if text_id: 
                break         
    
        self.build_units_database(
            db_name + ".db",
            text_id,
            constituents
        )




    #   SQL pipeline 
    
    
    # ==========================================================
    # create tables
    # ==========================================================
    
    def create_units_table(
            self,
            conn: sqlite3.Connection
            ) -> None:
        """
        Create all core database tables.
        """
    
        cur = conn.cursor()
    
        # -----------------------------------------
        # schema information
        # -----------------------------------------
    
        cur.execute("""
            CREATE TABLE IF NOT EXISTS database_info (
                schema_name TEXT NOT NULL,
                schema_version TEXT NOT NULL
            )
        """)
    
        cur.execute("""
            DELETE FROM database_info
        """)
    
        cur.execute("""
            INSERT INTO database_info
            VALUES ('TextToDB', '2.0')
        """)
    
        # -----------------------------------------
        # texts
        # -----------------------------------------
    
        cur.execute("""
            CREATE TABLE IF NOT EXISTS texts (
                text_id TEXT PRIMARY KEY
            )
        """)
    
        # -----------------------------------------
        # units
        # -----------------------------------------
    
        cur.execute("""
            CREATE TABLE IF NOT EXISTS units (
                unit_id TEXT PRIMARY KEY,
                parsed_text TEXT NOT NULL,
                surface_text TEXT NOT NULL
            )
        """)
    
        # -----------------------------------------
        # text <-> unit relation
        # -----------------------------------------
    
        cur.execute("""
            CREATE TABLE IF NOT EXISTS text_units (
                text_id TEXT NOT NULL,
                unit_id TEXT NOT NULL,
    
                FOREIGN KEY(text_id)
                    REFERENCES texts(text_id),
    
                FOREIGN KEY(unit_id)
                    REFERENCES units(unit_id), 
                    
                UNIQUE(text_id, unit_id)
            )
        """)
    
        # -----------------------------------------
        # lemma inventory
        # -----------------------------------------
    
        cur.execute("""
            CREATE TABLE IF NOT EXISTS lemmata (
                lemma_id INTEGER PRIMARY KEY,
                lemma TEXT UNIQUE NOT NULL
            )
        """)
    
        # -----------------------------------------
        # unit <-> lemma relation
        # -----------------------------------------
    
        cur.execute("""
            CREATE TABLE IF NOT EXISTS unit_lemmata (
                unit_id TEXT NOT NULL,
                lemma_id INTEGER NOT NULL,
    
                FOREIGN KEY(unit_id)
                    REFERENCES units(unit_id),
    
                FOREIGN KEY(lemma_id)
                    REFERENCES lemmata(lemma_id)
            )
        """)
    
        # -----------------------------------------
        # lemma realizations
        # -----------------------------------------
    
        cur.execute("""
            CREATE TABLE IF NOT EXISTS lemma_tokens (
                lemma_id INTEGER NOT NULL,
                token TEXT NOT NULL,
    
                FOREIGN KEY(lemma_id)
                    REFERENCES lemmata(lemma_id),
    
                UNIQUE (lemma_id, token)
            )
        """)
    
        conn.commit()
    
    
    # ==========================================================
    # units
    # ==========================================================
    
    def insert_units(
            self,
            conn: sqlite3.Connection,
            constituents: dict[str, dict]
            ) -> None:
        """
        Insert corpus units.
        """
    
        rows = [
            (
                unit_id,
                data["parsed_constituent"],
                data["surface_text"]
            )
            for unit_id, data in constituents.items()
        ]
    
        conn.executemany("""
            INSERT OR REPLACE INTO units
            (unit_id, parsed_text, surface_text)
            VALUES (?, ?, ?)
        """, rows)
    
        conn.commit()
    
    
    # ==========================================================
    # texts <-> units
    # ==========================================================
    
    def insert_text_units(
            self,
            conn: sqlite3.Connection,
            text_id: str,
            constituents: dict[str, dict]
            ) -> None:
        """
        Populate texts and text_units tables.
        """
    
        cur = conn.cursor()
    
        cur.execute("""
            INSERT OR IGNORE INTO texts
            (text_id)
            VALUES (?)
        """, (text_id,))
    
        rows = [
            (text_id, unit_id)
            for unit_id in constituents
        ]
    
        cur.executemany("""
            INSERT INTO text_units
            (text_id, unit_id)
            VALUES (?, ?)
        """, rows)
    
        conn.commit()
    
    
    # ==========================================================
    # lemma inventory
    # ==========================================================
    
    def insert_lemmata(
            self,
            conn: sqlite3.Connection,
            constituents: dict[str, dict]
            ) -> None:
        """
        Populate lemma inventory.
        """
    
        cur = conn.cursor()
    
        lemma_set = set()
    
        for data in constituents.values():
            lemma_set.update(data["lemmata"])
    
        rows = [
            (lemma,)
            for lemma in sorted(lemma_set)
        ]
    
        cur.executemany("""
            INSERT OR IGNORE INTO lemmata
            (lemma)
            VALUES (?)
        """, rows)
    
        conn.commit()
    
    
    # ==========================================================
    # unit <-> lemma relation
    # ==========================================================
    
    def insert_unit_lemmata(
            self,
            conn: sqlite3.Connection,
            constituents: dict[str, dict]
            ) -> None:
        """
        Populate unit_lemmata relation.
        """
    
        cur = conn.cursor()
    
        rows = []
    
        for unit_id, data in constituents.items():
    
            for lemma in set(data["lemmata"]):
    
                lemma_id = cur.execute("""
                    SELECT lemma_id
                    FROM lemmata
                    WHERE lemma = ?
                """, (lemma,)).fetchone()[0]
    
                rows.append(
                    (unit_id, lemma_id)
                )
    
        cur.executemany("""
            INSERT INTO unit_lemmata
            (unit_id, lemma_id)
            VALUES (?, ?)
        """, rows)
    
        conn.commit()
    
    
    # ==========================================================
    # lemma realizations
    # ==========================================================
    
    def insert_lemma_tokens(
            self,
            conn: sqlite3.Connection
            ) -> None:
        """
        Store all corpus realizations of each lemma.
        """
    
        cur = conn.cursor()
    
        rows = []
    
        for lemma, tokens in self._lemma_tokens.items():
    
            lemma_id = cur.execute("""
                SELECT lemma_id
                FROM lemmata
                WHERE lemma = ?
            """, (lemma,)).fetchone()[0]
    
            for token in set(tokens):
    
                rows.append(
                    (lemma_id, token)
                )
    
        cur.executemany("""
            INSERT OR IGNORE INTO lemma_tokens
            (lemma_id, token)
            VALUES (?, ?)
        """, rows)
    
        conn.commit()
    
    
    # ==========================================================
    # build database
    # ==========================================================
    
    def build_units_database(
            self,
            db_path: str,
            text_id: str,
            constituents: dict[str, dict]
            ) -> None:
        """
        Create and populate all database tables.
        """
    
        conn = sqlite3.connect(db_path)
    
        try:
    
            self.create_units_table(conn)
    
            self.insert_units(
                conn,
                constituents
            )
    
            self.insert_text_units(
                conn,
                text_id,
                constituents
            )
    
            self.insert_lemmata(
                conn,
                constituents
            )
    
            self.insert_unit_lemmata(
                conn,
                constituents
            )
    
            self.insert_lemma_tokens(
                conn
            )
    
        finally:
            conn.close()
    
    
    # # ==========================================================
    # # initialization
    # # ==========================================================
    
    # def initialize_textToDB(
    #         self,
    #         source_txt: str,
    #         db_name: str,
    #         text_id: str
    #         ) -> None:
    
    #     with open(source_txt, "r", encoding="utf-8") as f:
    #         txt_str = f.read()
    
    #     txt = " ".join(txt_str.split())
    #     txt = self._removePrologue(txt)
    
    #     constituents = self.getConstituents_andText(txt)
    
    #     self.build_units_database(
    #         db_name + ".db",
    #         text_id,
    #         constituents
    #     )
    
    
    





























