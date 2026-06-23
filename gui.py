#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 16 17:43:33 2026

@author: alexanderpfaff
"""


import sys
import io
import os  # Þurfum þetta til að lesa úr möppunni
 
from PyQt5.QtWidgets import ( 
    QApplication, QMainWindow, QWidget, QDialog, QInputDialog, QFileDialog, 
    QLineEdit, QPushButton, QMessageBox, QTextEdit, QGridLayout, 
    QHBoxLayout, QVBoxLayout, QLabel, QCheckBox, QSplitter, QAction, QRadioButton,
    QButtonGroup, QGroupBox

)
from PyQt5.QtGui import QColor, QPalette, QFont, QIntValidator, QRegExpValidator, QFontMetrics
from PyQt5.QtCore import Qt, QRegExp, QTimer

import sqlite3
from Arbor import Node, Tree, SearchForest, _matchLabel
from collections import Counter    




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
    





# class MainWindow_A(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Aðalgluggi með 3 panelum")
#         self.resize(900, 600)
        
#         # 1. Búum til miðlægja græju (Central Widget) fyrir QMainWindow
#         central_widget = QWidget(self)
#         self.setCentralWidget(central_widget)
        
#         # 2. Búum til láréttan splitter til að skipta glugganum í 3 hluta
#         # Athugaðu: Qt.Horizontal í PyQt5 breytist í Qt.Orientation.Horizontal
#         self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
#         # 3. Búum til panelana þrjá
#         self.left_panel = QWidget()
#         self.middle_panel = QWidget()
#         self.right_panel = QWidget()
        
#         # Gefum miðju og hægri panel lit til að sjá þá (verður breytt síðar)
#         self.middle_panel.setStyleSheet("background-color: #f0f0f0;")
#         self.right_panel.setStyleSheet("background-color: #e0e0e0;")
        
#         # 4. Setjum upp vinstri panelinn strax (Ræsing)
#         self.init_left_panel()
        
#         # 5. Setjum alla þrjá panelana inn í splitterinn
#         self.splitter.addWidget(self.left_panel)
#         self.splitter.addWidget(self.middle_panel)
#         self.splitter.addWidget(self.right_panel)
        
#         # Stillum hlutföllin (t.d. vinstri=20%, miðja=50%, hægri=30%)
#         self.splitter.setSizes([200, 500, 300])
        
#         # 6. Setjum splitterinn í aðal-útlit gluggans
#         main_layout = QHBoxLayout(central_widget)
#         main_layout.addWidget(self.splitter)
#         main_layout.setContentsMargins(0, 0, 0, 0) # Fjarlægir spássíur

#     def init_left_panel(self):
#         """Hér inni stillum við upp vinstri hliðinni."""
#         layout = QVBoxLayout(self.left_panel)
        
#         # Dæmi um titil og hnapp á vinstri hlið
#         title = QLabel("Stjórnborð")
#         title.setStyleSheet("font-weight: bold; font-size: 14px;")
        
#         btn_dialog = QPushButton("From SQL")
        
#         # Setjum í layoutið
#         layout.addWidget(title)
#         layout.addWidget(btn_dialog)
#         layout.addStretch() # Ýtir öllu upp

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = MainWindow_A()
#     window.show()
#     sys.exit(app.exec_())  
    
    
    
# input()
    

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PATTERNIZATION: treebank processor - PyQt5")
        self.resize(1000, 650)
        
        # 1. Miðlæg græja (Central Widget)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # 2. Splitter fyrir panelana þrjá
        self.splitter = QSplitter(Qt.Horizontal)
#        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.left_panel = QWidget()
        self.middle_panel = QTextEdit()  

        self.middle_panel.setReadOnly(True)  # Notandi getur ekki skrifað handvirkt í það
        self.middle_panel.setStyleSheet("background-color: #ffffff; font-family: Courier; font-size: 12px; border: 1px solid #ddd;")


        font = QFont("Courier New", 14)
        font.setStyleHint(QFont.Monospace)  # Neyðir kerfið til að velja jafnbreitt letur
        self.middle_panel.setFont(font)


        self.right_panel = QWidget() 
        self.right_panel.setMinimumWidth(350) 
        
        
        # Gefum miðju og hægri panel bakgrunnslit í bili
 #       self.middle_panel.setStyleSheet("background-color: #fcfcfc; border: 1px solid #ddd;")
   #     self.right_panel.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd;")
        
        # 3. Setjum upp valmyndina (MenuBar) efst
        self.init_menu_bar()
        
        # 4. Setjum upp vinstri & hægri panelinn
        self.init_left_panel()  
        
        self.init_right_panel() 
        
        # 5. Setjum allt saman í splitterinn
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.middle_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([200, 500, 300])  
        
        
        #  Tree navigation
        self.forest = None 
        self.tree_iter: int = -1
        
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.addWidget(self.splitter)
        main_layout.setContentsMargins(5, 5, 5, 5)   
        
        self.console_print("<b>NOTHING to see here.</b> please move along ...<br>", is_html=True)
        self.show()        
        
        self.show()



    ###########################################################################        
    # CONSOLE (print) -- middle_panel        
    def console_print(self, text, is_html=False):
        """Prentar texta og tryggir að jafnaður texti skakklast ekki."""
        if is_html:
            # Ef textinn inniheldur greinar (tré-skipulag), vefjum við honum í <pre>
            # til að tryggja að letrið verði Monospace og bil haldist rétt.
            if "├──" in str(text) or "└──" in str(text) or "   " in str(text):
                formatted_text = f"<pre style='font-family: Courier, Monospace; font-size: 14px;'>{text}</pre>"
                self.middle_panel.append(formatted_text)
            else:
                self.middle_panel.append(str(text))
        else:
            # Fyrir venjulegan texta breytum við honum í str
            self.middle_panel.append(str(text))
            
        # Skruna niður
        self.middle_panel.moveCursor(self.middle_panel.textCursor().MoveOperation.End)
        
        

    def _add_newLines(self, how_many=1) -> None:
        """
        Bætir við auðum línum í miðju-panelinn til að búa til pláss fyrir næsta úttak.
        @requires: how_many >= 1
        """
        # Öryggisvörn ef gildið er minna en 1
        if how_many < 1:
            return
            
        # Við keyrum lykkju eins oft og beðið er um
        for _ in range(how_many):
            self.middle_panel.append("")
            
        # Skrunar sjálfkrafa neðst eftir að línum er bætt við
        self.middle_panel.moveCursor(self.middle_panel.textCursor().MoveOperation.End)

    def _clear_display(self) -> None:
        """
        Hreinsar allan texta úr miðju-panelnum (display).
        """
        self.middle_panel.clear()

    ###########################################################################        






    ###########################################################################        
    #  left_panel        

    def init_menu_bar(self):
        """Býr til 'File' valmynd efst í glugganum."""
        menu_bar = self.menuBar()
        
        menu_bar.setNativeMenuBar(False)  # 🔥 Þetta neyðir valmyndina til að vera inni í glugganum (eins og á Windows)

        
        # Búum til 'File' flokkinn
        file_menu = menu_bar.addMenu("&File")
        
        # Aðgerð A: Open Single File
        # Athugið: QAction kemur beint úr QtWidgets í PyQt5 (en færðist í QtGui í PyQt6)
        open_file_action = QAction("&Open single file and convert to forest", self)
        open_file_action.setShortcut("Ctrl+O")
        open_file_action.triggered.connect(self.open_single_file)
        file_menu.addAction(open_file_action)
        
        # Aðgerð B: Open Folder
        open_folder_action = QAction("Open &folder and convert to forest", self)
        open_folder_action.setShortcut("Ctrl+Shift+O")
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)

        # Aðgerð C: Open sql db
        open_db_action = QAction("From S&QL", self)
        open_db_action.setShortcut("Ctrl+Q")
        open_db_action.triggered.connect(self.open_sqlDB)
        file_menu.addAction(open_db_action)
        
        
        # Loka valmöguleiki
        exit_action = QAction("&Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def init_left_panel(self):
        """Hér inni stillum við upp vinstri hliðinni."""
        layout = QVBoxLayout(self.left_panel)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Aðgerðir")
        title.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        layout.addWidget(title)
        
        btn_next_tree = QPushButton("Next")
        btn_next_tree.clicked.connect(self.nextTree)
        layout.addWidget(btn_next_tree)
        
        btn_previous_tree = QPushButton("Previous")
        btn_previous_tree.clicked.connect(self.previousTree)
        layout.addWidget(btn_previous_tree)
        
        layout.addStretch() 
        
        btn_text = QPushButton("Text")
        btn_text.clicked.connect(self.getText)
        layout.addWidget(btn_text)
        
        
        btn_dyck = QPushButton("Dyck")
        btn_dyck.clicked.connect(self.getDyck)
        layout.addWidget(btn_dyck)
        
        
        btn_dyck_cat = QPushButton("Dyck+Cat")
        btn_dyck_cat.clicked.connect(self.getDyckCat)
        layout.addWidget(btn_dyck_cat)
        
        
        btn_kids = QPushButton("Get the kids")
        btn_kids.clicked.connect(self.get_immediate_children)
        layout.addWidget(btn_kids)
        
        layout.addStretch()  
        
        
        patternize = QPushButton("patternize!")
        patternize.clicked.connect(self.open_patternize)
        layout.addWidget(patternize)
        
        layout.addStretch()  
        
        self.forest_ID = QLabel("")
        self.forest_ID.setStyleSheet("font-size: 13px; color: #333;")
        layout.addWidget(self.forest_ID)

        self.counter = QLabel("")
        self.counter.setStyleSheet("font-size: 13px; color: #333;")
        layout.addWidget(self.counter)


    # --- Virkni fyrir skráameðhöndlun (Slots) ---

    def open_single_file(self):
        """Sækir eina tiltekna skrá."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Choose a file", "", "Parsed text file (*.psd);;All files (*)"
        )
        if file_path:
            # Hér prentum við slóðina í bili (getum sent hana í miðju-panel síðar)
            print(f"Hleð inn skrá: {file_path}")
            
            # Sýnum staðfestingu
            file_name = os.path.basename(file_path)
            QMessageBox.information(self, "Skrá hlaðin", f"Tókst að hlaða inn skránni:\n{file_name}") 
            
            # Glugginn opnast, fangar inntak og skilar gildinu í 'value' 
            value, ok = QInputDialog.getText(self, "Name of prospective sql database", 
                                             "Enter a name for the db:") 
            
            if ok and value:
                self.console_print(f"Notandi skrifaði: {value}")


        

    def open_sqlDB(self):
        """Sækir eina tiltekna skrá."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Choose a file", "", "SQLite db file (*.db);;All files (*)"
        )
        if file_path:
            # Hér prentum við slóðina í bili (getum sent hana í miðju-panel síðar)
            print(f"Hleð inn skrá: {file_path}")
            
            # Sýnum staðfestingu
            file_name = os.path.basename(file_path)
            QMessageBox.information(self, "Skrá hlaðin", f"Tókst að hlaða inn skránni:\n{file_name}") 
            
        data = getParsedTextWithIDs(file_path)
        self.forest = SearchForest(data)  
        
        # # just testin ...
        # self._clear_display()
        # self.console_print(" \n ")
        # tst_str = str(self.forest.forest[2]) 
        # self.console_print(tst_str, is_html=True) 
        # print(tst_str) 
        # self._add_newLines()
        self.nextTree()





    def open_folder(self):
        """Sækir möppu og finnur allar skrár inni í henni."""
        folder_path = QFileDialog.getExistingDirectory(self, "Veldu möppu með gögnum")
        
        if folder_path:
            print(f"Valin mappa: {folder_path}")
            
            # Finnum allar skrár inni í möppunni (síað burt undirmöppur)
            all_files = []
            try:
                for item in os.listdir(folder_path):
                    full_path = os.path.join(folder_path, item)
                    if os.path.isfile(full_path):
                        all_files.append(item)
            except Exception as e:
                QMessageBox.critical(self, "Villa", f"Gat ekki lesið möppu:\n{e}")
                return
            
            # Prentum listann af skránum í stjórnborðið
            print(f"Fann {len(all_files)} skrár:")
            for f in all_files:
                print(f" - {f}")
                
            # Sýnum notandanum niðurstöðu
            QMessageBox.information(
                self, 
                "Mappa hlaðin", 
                f"Tókst að lesa möppu!\nFjöldi skráa sem fundust: {len(all_files)}"
            )






    ######################################################################################
    ###     iterators / internal tree collection 
    def nextTree(self) -> None: 
        if self.forest and self.forest.forest: 
            
            self.tree_iter += 1
            if self.tree_iter >= len(self.forest.forest): 
                self.tree_iter = 0
            tree = self.forest.forest[self.tree_iter]  

            self._clear_display()
            self.console_print("  ")
            self.console_print(f"<b>{str(tree.ID)} </b>  <br>", is_html=True)
    
            self.console_print(str(tree), is_html=True) 
            self._add_newLines(3)  
            self.console_print(f"{tree.tree_rel} \n")
            self.console_print(f"{tree.source} \n")
            self.console_print(f"{tree.target} \n")     
            
            self.forest_ID.setText(f"{tree.text_ID}")
            self.counter.setText(f"{self.tree_iter + 1} / {len(self.forest.forest)}")
                    


    def previousTree(self) -> None: 
        if self.forest and self.forest.forest: 
            
            self.tree_iter -= 1
            if self.tree_iter <0: 
                self.tree_iter =  len(self.forest.forest) - 1
            tree = self.forest.forest[self.tree_iter]  

            self._clear_display()
            self.console_print("  ")
            self.console_print(f"<b>{str(tree.ID)} </b>  <br>", is_html=True)
    
            self.console_print(str(tree), is_html=True) 
            self._add_newLines(3) 
            self.console_print(f"{tree.tree_rel} \n")
            self.console_print(f"{tree.source} \n")
            self.console_print(f"{tree.target} \n")
            
            self.forest_ID.setText(f"{tree.text_ID}")
            self.counter.setText(f"{self.tree_iter + 1} / {len(self.forest.forest)}")
                    


    def getText(self) -> None: 
        if self.forest and self.forest.forest: 
            tree = self.forest.forest[self.tree_iter]              
            self.console_print(tree.root.get_terminalSequence() + " ", is_html=False) 
            self._add_newLines(3) 
            

    def getDyck(self) -> None: 
        if self.forest and self.forest.forest: 
            tree = self.forest.forest[self.tree_iter]              
            self.console_print(tree.root.dyck_naked() + " ", is_html=False) 
            self._add_newLines(3) 
            

    def getDyckCat(self) -> None: 
        if self.forest and self.forest.forest: 
            tree = self.forest.forest[self.tree_iter]              
            self.console_print(tree.root.dyck_catLabels() + " ", is_html=False) 
            self._add_newLines(3) 
            


    def get_immediate_children(self) -> None: 
        if self.forest and self.forest.forest:         
            tree = self.forest.forest[self.tree_iter]  
            if tree.root.children:  
                self.console_print("  ")
                self.console_print("IMMEDIATE CHILDREN: <br>", is_html=True) 
                for kid in tree.root.children: 
                    self.console_print(str(Tree(kid)), is_html=True) 
                    self._add_newLines(2) 
                    


    
    def open_patternize(self):
        # Skilgreinum gluggann sem klasastigsbreytu (self.workspace)
        # svo Python eyði honum ekki úr minni (Garbage Collection)
        self.workspace = Patternization(parent=self) 
        self.workspace.show() # NOTA .show() en ekki .exec_(), þannig er hann lifandi og sjálfstæður!






    ######################################################################################
    # right panel: queries
    def init_right_panel(self):
        """Hér inni stillum við upp hægri hliðinni."""
        layout = QVBoxLayout(self.right_panel)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10) 
        
        self.q_forest: SearchForest = None 
        self.q_tree_iter: int = -1
        self.q_forest_ID: str
        self.q_counter: int
        
        
        
        title = QLabel("Search and prune")
        title.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        layout.addWidget(title)
        
        #  Q1 1   
        q1_layout = QHBoxLayout() 
        q1_source = QLineEdit() 
        q1_source.setPlaceholderText("ROOT")
        q1_source.setReadOnly(True)
        btn_root_dom_cat = QPushButton("dominates")
        btn_root_dom_cat.clicked.connect(self.root_dominates_cat) #### to do!
        self.q1_target = QLineEdit()  
        self.q1_target.setPlaceholderText("cat/label")
        q1_extra = QLabel("       ")
        
        q1_layout.addWidget(q1_source)
        q1_layout.addWidget(btn_root_dom_cat)
        q1_layout.addWidget(self.q1_target)
        q1_layout.addWidget(q1_extra)

        layout.addLayout(q1_layout)   
        
        
        #  Q2   
        q2_layout = QHBoxLayout() 
        q2_source = QLineEdit() 
        q2_source.setPlaceholderText("ROOT")
        q2_source.setReadOnly(True)
        btn_root_dom_lemma = QPushButton("dominates")
        btn_root_dom_lemma.clicked.connect(self.root_dominates_lemma) #### to do!
        self.q2_target = QLineEdit()  
        self.q2_target.setPlaceholderText("lemma")
        q2_extra = QLabel("       ")
        
        q2_layout.addWidget(q2_source)
        q2_layout.addWidget(btn_root_dom_lemma)
        q2_layout.addWidget(self.q2_target)
        q2_layout.addWidget(q2_extra)

        layout.addLayout(q2_layout)   
        
        
        
         
        #  Q3   
        q3_layout = QHBoxLayout() 
        self.q3_source = QLineEdit() 
        self.q3_source.setPlaceholderText("cat/label")
        btn_cat_dom_cat = QPushButton("dominates")
        btn_cat_dom_cat.clicked.connect(self.cat_dominates_cat) #### to do!
        self.q3_target = QLineEdit()  
        self.q3_target.setPlaceholderText("cat/label")
        q3_extra = QLabel("       ")
        
        q3_layout.addWidget(self.q3_source)
        q3_layout.addWidget(btn_cat_dom_cat)
        q3_layout.addWidget(self.q3_target)
        q3_layout.addWidget(q3_extra)

        layout.addLayout(q3_layout)   
        



##########
        
        groupbox_dom = QGroupBox("Domination Mode") 
        self.domination_group = QButtonGroup()

        general = QRadioButton("generally")
        general.setChecked(True)
        immediate = QRadioButton("immediately")
        minimal = QRadioButton("minimally")
        
        self.domination_group.addButton(general, 0)
        self.domination_group.addButton(immediate, 1)
        self.domination_group.addButton(minimal, 2)
        dom_rb_layout = QHBoxLayout()
        dom_rb_layout.addWidget(general)
        dom_rb_layout.addWidget(immediate)
        dom_rb_layout.addWidget(minimal)
        
        groupbox_dom.setLayout(dom_rb_layout)
        
        layout.addWidget(groupbox_dom)   
        layout.addWidget(QLabel(" "))   
        



############


        
        #  Q4   
        q4_layout = QHBoxLayout() 
        self.q4_source = QLineEdit() 
        self.q4_source.setPlaceholderText("cat/label")
        btn_cat_com_cat = QPushButton("c-commands")
        btn_cat_com_cat.clicked.connect(self.cat_c_commands_cat) #### to do!
        self.q4_target = QLineEdit()  
        self.q4_target.setPlaceholderText("cat/label")
        q4_extra = QLabel("       ")
        
        q4_layout.addWidget(self.q4_source)
        q4_layout.addWidget(btn_cat_com_cat)
        q4_layout.addWidget(self.q4_target)
        q4_layout.addWidget(q4_extra)

        layout.addLayout(q4_layout)   
        
        layout.addWidget(QLabel(" "))   


        
        #  q5   
        q5_layout = QHBoxLayout() 
        q5b_layout = QHBoxLayout() 
        q5c_layout = QHBoxLayout() 
        self.q5_source = QLineEdit() 
        self.q5_source.setPlaceholderText("cat/label")
        btn_cat_precedes_cat = QPushButton("precedes")
        btn_cat_precedes_cat.clicked.connect(self.cat_precedes_cat) #### to do!
        self.q5_target = QLineEdit()  
        self.q5_target.setPlaceholderText("cat/label")

        q5_layout.addWidget(self.q5_source)
        q5_layout.addWidget(btn_cat_precedes_cat)
        q5_layout.addWidget(self.q5_target) 

        q5_level_label = QLabel("Level difference: ") 
        self.q5_level = QLineEdit() 
        max_rb = QRadioButton("@max")
        exact_rb = QRadioButton("@exactly")
        max_rb.setChecked(True) 
        self.levelDiff = QButtonGroup()
        self.levelDiff.addButton(max_rb, 0)
        self.levelDiff.addButton(exact_rb, 1)
        self.q5_level.setPlaceholderText("level difference") 
        self.q5_level.setText("10") 
        self.q5_level.setValidator(QIntValidator(0, 100))
        
        q5b_layout.addWidget(q5_level_label)
        q5b_layout.addWidget(max_rb)
        q5b_layout.addWidget(exact_rb)
        q5b_layout.addWidget(self.q5_level)



        q5_label_ancestry = QLabel("Ancestral distance: ")
        self.q5_ancestry = QLineEdit()
        self.q5_ancestry.setPlaceholderText("ancestral_distance")
        self.q5_ancestry.setText("10") 
        self.q5_ancestry.setValidator(QIntValidator(1, 100))
        
        
        q5c_layout.addWidget(q5_label_ancestry)
        q5c_layout.addStretch()
        q5c_layout.addWidget(self.q5_ancestry)

        layout.addLayout(q5_layout)   
        layout.addLayout(q5b_layout)   
        layout.addLayout(q5c_layout)   
        


        layout.addStretch()


        #  q6   
        q6_layout = QHBoxLayout()  
        prune_btn = QPushButton("PRUNE!")
        prune_btn.clicked.connect(self.prune) 
        
        q6_layout.addStretch()
        q6_layout.addWidget(prune_btn)
        q6_layout.addStretch()

        layout.addLayout(q6_layout)   

        layout.addStretch()



        
        groupbox = QGroupBox("Output Mode") 
        self.output_group = QButtonGroup()

        full_trees_rb = QRadioButton("IDs only")
        pruned_trees_rb = QRadioButton("pruned sub-trees")
        full_trees_rb.setChecked(True)
        
        self.output_group.addButton(full_trees_rb, 1)
        self.output_group.addButton(pruned_trees_rb, 0)
        rb_layout = QHBoxLayout()
        rb_layout.addWidget(full_trees_rb)
        rb_layout.addWidget(pruned_trees_rb)
        
        groupbox.setLayout(rb_layout)
        
        layout.addWidget(groupbox)   
        
        
        
        btn_layout = QHBoxLayout() 
        btn_layout.addStretch()
        btn_next_tree = QPushButton(" qNext ")
        btn_next_tree.clicked.connect(self.next_qTree)
        btn_previous_tree = QPushButton("qPrevious")
        btn_previous_tree.clicked.connect(self.previous_qTree)  
        btn_layout.addWidget(btn_previous_tree)
        btn_layout.addWidget(btn_next_tree)
        btn_layout.addStretch()  
        layout.addLayout(btn_layout)
        
        layout.addStretch() 

        self.q_forest_ID = QLabel("")
        self.q_forest_ID.setStyleSheet("font-size: 13px; color: #333;")
        layout.addWidget(self.q_forest_ID)

        self.q_counter = QLabel("")
        self.q_counter.setStyleSheet("font-size: 13px; color: #333;")
        layout.addWidget(self.q_counter)

          
        
        
        
    
    def root_dominates_cat(self): 
        value = self.output_group.checkedId() 
        print(value)

        if not self.forest:
            return 
        self._q_clear()


        pass
        # self.q_forest
            
        
    
    def root_dominates_lemma(self): 
        v = self.domination_group.checkedId()  
        print(v)

        if not self.forest:
            return 
        self._q_clear() 
        
        
        pass
        # self.q_forest
            
    def cat_dominates_cat(self) -> None: 
        source = self.q3_source.text()
        target = self.q3_target.text()  
        if not self.forest or not source or not target:
            return 
        self._q_clear()
        
        func = [self.forest.cat_dominates_cat, 
                self.forest.cat_immediately_dominates_cat, 
                self.forest.cat_minimally_dominates_cat][self.domination_group.checkedId()]  
        
        relation = ["dominates", 
                    "dominates_immediately", 
                    "dominates_minimally"][self.domination_group.checkedId()]  
        relation = f"{source} {relation} {target}"
        
        id_only = bool(self.output_group.checkedId()) 
        dom_data = func(source, target)  
        
        if id_only:  
            self._get_full_forest(dom_data, relation)
        else: 
            self._get_pruned_forest(dom_data, relation)

        self.next_qTree()
            
        
    def cat_c_commands_cat(self) -> None:
        source = self.q4_source.text()
        target = self.q4_target.text()  
        if not self.forest or not source or not target:
            return 
        self._q_clear() 
        relation = f"{source} c-commands {target}"
        id_only = bool(self.output_group.checkedId()) 
        com_data = self.forest.cat_c_commands_cat(source, target) 

        if id_only:  
            self._get_full_forest(com_data, relation)
        else: 
            self._get_pruned_forest(com_data, relation)

        self.next_qTree()


    def cat_precedes_cat(self) -> None:  
        source = self.q5_source.text().strip()
        target = self.q5_target.text().strip()
        if not self.forest or not source or not target:
            return
        if not self.q5_level.text() or not self.q5_ancestry.text():
            return
        level_diff = int(self.q5_level.text())
        ancestry   = int(self.q5_ancestry.text())          
        self._q_clear() 
        
        relation = f"{source} precedes {target}"        
        id_only = bool(self.output_group.checkedId())  
        
        func = [self.forest.precedes_atMax, 
                self.forest.precedes_atExactly][self.levelDiff.checkedId()]
        
        prec_data = func(source, target, diff=level_diff, ancestral_distance=ancestry) 
        
        if id_only:  
            self._get_full_forest(prec_data, relation)
        else: 
            self._get_pruned_forest(prec_data, relation)

        self.next_qTree()
         
        
        
        
    def _get_full_forest(self, data: dict[str, list[tuple[Node, Node]]], relation: str) -> None: 
        relevant_trees = []
        for tree in self.forest.forest: 
            if tree.ID in data.keys():
                tree.tree_rel = relation
                sources, targets = zip(*data[tree.ID])  
                sources = [s.key for s in sources] 
                targets = [t.key for t in targets]
                tree.source = str(sources)[1:-1]
                tree.target = str(targets)[1:-1]
                relevant_trees.append(tree)
        self.q_forest = SearchForest.from_trees(relevant_trees) 
        


    def _get_pruned_forest(self, data: dict[str, list[tuple[Node, Node]]], relation: str) -> None: 
        relevant_trees = []
        for tree in self.forest.forest: 
            if tree.ID in data.keys():
                for source, target in data[tree.ID]: 
                    if "c-commands" in relation:
                        qtree = Tree(source.parent) 
                    elif "precedes" in relation:       
                        qtree = Tree(source.get_minimal_commonAncestor(target)) 
                    else:
                        qtree = Tree(source) 
                    qtree.source = source.key 
                    qtree.target = target.key 
                    qtree.tree_rel = relation 
                    qtree._id = tree.ID 
                    qtree._text_id = tree.text_ID
                    relevant_trees.append(qtree)
        self.q_forest = SearchForest.from_trees(relevant_trees) 
        print(len(relevant_trees))
        print(self.q_forest.size)



    def _get_prefix_R(self, tree: Tree): 
        prefix = "" if not tree.tree_rel else ' # '
        return tree.tree_rel + prefix

    def _get_prefix_S(self, tree: Tree): 
        prefix = "" if not tree.source else ' # '
        return tree.source + prefix

    def _get_prefix_T(self, tree: Tree): 
        prefix = "" if not tree.target else ' # '
        return tree.target + prefix






    def prune(self) -> None: 
        if not self.q_forest or not self.q_forest.forest:
            return 
        self.forest = self.q_forest 
        self._q_clear()
        self._q_setZero()
        self.tree_iter = -1 
        self.nextTree()
        
        
        


    ######################################################################################
    ###   query  iterators / internal tree collection 
    def next_qTree(self) -> None: 
        if self.q_forest and self.q_forest.forest: 
            
            self.q_tree_iter += 1
            if self.q_tree_iter >= len(self.q_forest.forest): 
                self.q_tree_iter = 0
            tree = self.q_forest.forest[self.q_tree_iter]  

            self._clear_display()
            self.console_print("  ")
            self.console_print(f"<b>{str(tree.ID)} </b>  <br>", is_html=True)
    
            self.console_print(str(tree), is_html=True) 
            self._add_newLines(3)  
            self.console_print(f"Relation:  {tree.tree_rel} \n")
            self.console_print(f"Source:    {tree.source} \n")
            self.console_print(f"Target:    {tree.target} \n")
            
            self.q_forest_ID.setText(f"{tree.text_ID}")
            self.q_counter.setText(f"{self.q_tree_iter + 1} / {len(self.q_forest.forest)}")
                    


    def previous_qTree(self) -> None: 
        if self.q_forest and self.q_forest.forest: 
            
            self.q_tree_iter -= 1
            if self.q_tree_iter <0: 
                self.q_tree_iter =  len(self.q_forest.forest) - 1
            tree = self.q_forest.forest[self.q_tree_iter]  

            self._clear_display()
            self.console_print("  ")
            self.console_print(f"<b>{str(tree.ID)} </b>  <br>", is_html=True)
    
            self.console_print(str(tree), is_html=True) 
            self._add_newLines(3) 
            self.console_print(f"Relation:  {tree.tree_rel} \n")
            self.console_print(f"Source:    {tree.source} \n")
            self.console_print(f"Target:    {tree.target} \n")
            
            self.q_forest_ID.setText(f"{tree.text_ID}")
            self.q_counter.setText(f"{self.q_tree_iter + 1} / {len(self.q_forest.forest)}") 
            
            
    def _q_clear(self) -> None: 
        self.q_forest: SearchForest = SearchForest(None, True) 
        self.q_tree_iter: int = -1
        self.q_forest_ID: str
        self.q_counter: int
        self.q_counter.setText("") 
        self.q_forest_ID.clear()
#        self.q_counter.setText(f"{self.q_tree_iter + 1} / {len(self.q_forest.forest)}")  
        self._clear_display()
        
    def _q_setZero(self) -> None: 
        self.q1_target.clear()
        self.q2_target.clear()
        self.q3_source.clear()
        self.q3_target.clear()
        self.q4_source.clear()
        self.q4_target.clear()
        self.q5_source.clear()
        self.q5_target.clear()
        self.q5_ancestry.setText("42")
        self.q5_level.setText("7")
        
        
                    


    ######################################################################################





class Patternization(QWidget): 
    def __init__(self, parent=None):
        
        super().__init__(parent)
        self.setWindowTitle("Patternize")
        self.resize(500, 600) 
        
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)  
        
        self.get_patt_simple = QPushButton("Simple Patterns") 
        self.get_patt_simple.clicked.connect(self.getPattern_1)


        patt_1 = QHBoxLayout()
        patt_1.addStretch()
        patt_1.addWidget(self.get_patt_simple)  
        patt_1.addStretch() 
        layout.addLayout(patt_1)
        
        
    def getPattern_1(self) -> None: 
        forest = self.parent().forest.forest[:]
        if not forest: 
            return 
        print("Patternize -- hooray! ") 
        self.parent()._clear_display()
    
    
        exceptions = ["PP", "CP", "CONJP", "NP-COM", "NP-ATR", "NP-PRN", "NP-POS"]  
        
        candidates = ["N", "ADJ", "PP", "CP", "CONJP", "PRO-GEN", "D", "NP-COM", "NP-ATR", "NP-PRN", "NP-POS"]
        
        descend = lambda n, l: not any(_matchLabel(n.label, exc) for exc in exceptions)  
        
        include = lambda n, l: any(_matchLabel(n.label, cand) for cand in candidates)
        
        patterns_n = []
        patterns_l = []
        for tree in forest: 
            node = tree.root 
            pattern_labels = [ n.label 
                              for n in node.walk(include=include, descend=descend)] 
            
            # patterns_n.append(pattern_node)
            patterns_l.append(tuple(pattern_labels))


        c = dict(Counter(patterns_l))

        print(f"Patterns found: {len(patterns_l)}")
        for patt in c: 
            print(patt)
            self.parent().console_print(f"{patt} : {c[patt]}") 
            self.parent()._add_newLines(2)









    ######################################################################################







if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())  
    














