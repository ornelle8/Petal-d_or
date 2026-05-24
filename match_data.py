import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# ─────────────────────────────────────────────
#  Base de données en mémoire
# ─────────────────────────────────────────────
conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.executescript("""
CREATE TABLE JOUEUR (
    id_joueur       INTEGER PRIMARY KEY,
    nom             TEXT NOT NULL,
    poste           TEXT NOT NULL,
    age             INTEGER NOT NULL,
    equipe          TEXT NOT NULL
);

CREATE TABLE MATCH_F (
    id_match        INTEGER PRIMARY KEY,
    date_match      TEXT NOT NULL,
    stade           TEXT NOT NULL
);

CREATE TABLE PASSER (
    id_passe        INTEGER PRIMARY KEY,
    id_match        INTEGER NOT NULL,
    id_joueur_source INTEGER NOT NULL,
    id_joueur_dest  INTEGER NOT NULL,
    minute          INTEGER NOT NULL,
    FOREIGN KEY (id_match)          REFERENCES MATCH_F(id_match),
    FOREIGN KEY (id_joueur_source)  REFERENCES JOUEUR(id_joueur),
    FOREIGN KEY (id_joueur_dest)    REFERENCES JOUEUR(id_joueur)
);

CREATE TABLE TIR (
    id_tir      INTEGER PRIMARY KEY,
    id_joueur   INTEGER NOT NULL,
    id_match    INTEGER NOT NULL,
    cadre       INTEGER NOT NULL DEFAULT 0,
    but         INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (id_joueur) REFERENCES JOUEUR(id_joueur),
    FOREIGN KEY (id_match)  REFERENCES MATCH_F(id_match)
);
""")
conn.commit()

# ─────────────────────────────────────────────
#  Requêtes prédéfinies
# ─────────────────────────────────────────────
QUERIES = {
    "Partie A": [
        ("A.2 — Noms commençant par 'A'",
         "SELECT * FROM JOUEUR WHERE nom LIKE 'A%';"),
        ("A.3 — Joueurs âgés entre 20 et 30 ans",
         "SELECT * FROM JOUEUR WHERE age BETWEEN 20 AND 30;"),
        ("A.4 — Défenseurs ou milieux",
         "SELECT * FROM JOUEUR WHERE poste IN ('défenseur', 'milieu');"),
    ],
    "Partie B": [
        ("B.1 — Nombre de passes par joueur",
         """SELECT J.nom, COUNT(*) AS total_passes
FROM PASSER P JOIN JOUEUR J ON J.id_joueur = P.id_joueur_source
GROUP BY P.id_joueur_source ORDER BY total_passes DESC;"""),
        ("B.2 — Joueurs ayant fait une passe OU un tir",
         """SELECT DISTINCT J.id_joueur, J.nom, J.poste FROM JOUEUR J
WHERE J.id_joueur IN (SELECT id_joueur_source FROM PASSER)
   OR J.id_joueur IN (SELECT id_joueur FROM TIR)
ORDER BY J.id_joueur;"""),
        ("B.3 — Joueurs ayant fait des passes ET des tirs",
         """SELECT DISTINCT J.id_joueur, J.nom, J.poste FROM JOUEUR J
WHERE J.id_joueur IN (SELECT id_joueur_source FROM PASSER)
  AND J.id_joueur IN (SELECT id_joueur FROM TIR)
ORDER BY J.id_joueur;"""),
        ("B.4 — Passes sans aucun tir",
         """SELECT DISTINCT J.id_joueur, J.nom, J.poste FROM JOUEUR J
WHERE J.id_joueur IN (SELECT id_joueur_source FROM PASSER)
  AND J.id_joueur NOT IN (SELECT id_joueur FROM TIR)
ORDER BY J.id_joueur;"""),
    ],
}

# ─────────────────────────────────────────────
#  Palette de couleurs
# ─────────────────────────────────────────────
BG        = "#0f1117"
BG2       = "#1a1d27"
BG3       = "#23263a"
ACCENT    = "#4f8ef7"
ACCENT2   = "#3ecf8e"
TEXT      = "#e8eaf0"
TEXT2     = "#8b90a7"
DANGER    = "#f0654a"
BORDER    = "#2e3248"
FONT_MONO = ("Courier New", 11)
FONT_UI   = ("Segoe UI", 10)
FONT_H    = ("Segoe UI", 12, "bold")
FONT_SM   = ("Segoe UI", 9)

# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────
def run_query(sql):
    try:
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        return cols, rows, None
    except Exception as e:
        return [], [], str(e)

def show_results(tree, cols, rows, error=None):
    tree.delete(*tree.get_children())
    tree["columns"] = []
    if error:
        tree["columns"] = ("err",)
        tree.heading("err", text="Erreur")
        tree.column("err", width=600)
        tree.insert("", "end", values=(error,), tags=("err",))
        tree.tag_configure("err", foreground=DANGER)
        return
    tree["columns"] = cols
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=max(80, 600 // max(len(cols), 1)), anchor="w")
    for i, row in enumerate(rows):
        tag = "even" if i % 2 == 0 else "odd"
        tree.insert("", "end", values=list(row), tags=(tag,))
    tree.tag_configure("even", background=BG2)
    tree.tag_configure("odd",  background=BG3)

# ─────────────────────────────────────────────
#  Fenêtre principale
# ─────────────────────────────────────────────
root = tk.Tk()
root.title("Exercice 1 — Base de données Football  |  IUT Douala")
root.configure(bg=BG)
root.geometry("1100x750")
root.minsize(900, 600)

# Style ttk
style = ttk.Style()
style.theme_use("clam")
style.configure("TNotebook",       background=BG,  borderwidth=0)
style.configure("TNotebook.Tab",   background=BG3, foreground=TEXT2,
                font=FONT_UI, padding=[14, 6])
style.map("TNotebook.Tab",
          background=[("selected", ACCENT)],
          foreground=[("selected", "#ffffff")])
style.configure("Treeview",        background=BG2, foreground=TEXT,
                fieldbackground=BG2, rowheight=26, font=FONT_UI)
style.configure("Treeview.Heading", background=BG3, foreground=ACCENT,
                font=("Segoe UI", 10, "bold"), relief="flat")
style.map("Treeview", background=[("selected", ACCENT)])
style.configure("Vertical.TScrollbar", background=BG3, troughcolor=BG)
style.configure("Horizontal.TScrollbar", background=BG3, troughcolor=BG)

# ── En-tête ─────────────────────────────────
header = tk.Frame(root, bg=BG, pady=14, padx=20)
header.pack(fill="x")
tk.Label(header, text="⚽  Base de données Football",
         bg=BG, fg=TEXT, font=("Segoe UI", 16, "bold")).pack(side="left")
tk.Label(header, text="IUT Douala — Génie Informatique",
         bg=BG, fg=TEXT2, font=FONT_SM).pack(side="right", pady=6)

sep = tk.Frame(root, bg=BORDER, height=1)
sep.pack(fill="x")

# ── Notebook principal ───────────────────────
nb = ttk.Notebook(root)
nb.pack(fill="both", expand=True, padx=0, pady=0)

# ═══════════════════════════════════════════════
#  ONGLET 1 — Saisie des données
# ═══════════════════════════════════════════════
tab_data = tk.Frame(nb, bg=BG)
nb.add(tab_data, text="  📥  Saisie des données  ")

# Sous-notebook pour chaque table
nb_tables = ttk.Notebook(tab_data)
nb_tables.pack(fill="both", expand=True, padx=10, pady=10)

def make_label(parent, text, row, col, bold=False):
    f = FONT_H if bold else FONT_UI
    tk.Label(parent, text=text, bg=BG2, fg=TEXT2 if not bold else ACCENT,
             font=f).grid(row=row, column=col, sticky="w", padx=8, pady=4)

def make_entry(parent, row, col, width=20):
    e = tk.Entry(parent, bg=BG3, fg=TEXT, insertbackground=TEXT,
                 font=FONT_MONO, width=width, relief="flat",
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT)
    e.grid(row=row, column=col, padx=8, pady=4, sticky="w")
    return e

def make_btn(parent, text, cmd, color=ACCENT):
    return tk.Button(parent, text=text, command=cmd,
                     bg=color, fg="#ffffff", font=FONT_UI,
                     relief="flat", padx=14, pady=6, cursor="hand2",
                     activebackground=BG3, activeforeground=TEXT)

def make_tree_frame(parent):
    frame = tk.Frame(parent, bg=BG2)
    tree = ttk.Treeview(frame, show="headings", selectmode="browse")
    vsb = ttk.Scrollbar(frame, orient="vertical",   command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    return frame, tree

# ── Table JOUEUR ────────────────────────────
t_joueur = tk.Frame(nb_tables, bg=BG2)
nb_tables.add(t_joueur, text="  JOUEUR  ")

form_j = tk.Frame(t_joueur, bg=BG2, pady=10, padx=10)
form_j.pack(fill="x")

labels_j = ["ID joueur", "Nom", "Poste", "Âge", "Équipe"]
entries_j = []
for i, lbl in enumerate(labels_j):
    make_label(form_j, lbl, 0, i)
    e = make_entry(form_j, 1, i, 14)
    entries_j.append(e)

# Combobox pour poste
entries_j[2].destroy()
postes_var = tk.StringVar()
cb_poste = ttk.Combobox(form_j, textvariable=postes_var, width=13,
                         values=["attaquant","milieu","défenseur","gardien"],
                         font=FONT_UI, state="normal")
cb_poste.grid(row=1, column=2, padx=8, pady=4, sticky="w")
entries_j[2] = cb_poste

tree_j_frame, tree_j = make_tree_frame(t_joueur)
tree_j_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

def refresh_joueur():
    cols, rows, err = run_query("SELECT * FROM JOUEUR;")
    show_results(tree_j, cols, rows, err)
    tree_j["columns"] = cols or []
    for c in (cols or []):
        tree_j.heading(c, text=c)
        tree_j.column(c, width=120, anchor="w")

def add_joueur():
    vals = [e.get().strip() for e in entries_j]
    if not all(vals):
        messagebox.showwarning("Champ manquant", "Remplis tous les champs.")
        return
    try:
        cur.execute("INSERT INTO JOUEUR VALUES (?,?,?,?,?)",
                    (int(vals[0]), vals[1], vals[2], int(vals[3]), vals[4]))
        conn.commit()
        for e in entries_j:
            if hasattr(e, 'delete'):
                e.delete(0, tk.END)
        refresh_joueur()
    except Exception as ex:
        messagebox.showerror("Erreur", str(ex))

def del_joueur():
    sel = tree_j.selection()
    if not sel:
        return
    row = tree_j.item(sel[0])["values"]
    cur.execute("DELETE FROM JOUEUR WHERE id_joueur=?", (row[0],))
    conn.commit()
    refresh_joueur()

btn_frame_j = tk.Frame(t_joueur, bg=BG2, pady=6, padx=10)
btn_frame_j.pack(fill="x")
make_btn(btn_frame_j, "➕  Ajouter", add_joueur).pack(side="left", padx=(0,8))
make_btn(btn_frame_j, "🗑  Supprimer sélection", del_joueur, DANGER).pack(side="left")

# ── Table MATCH ─────────────────────────────
t_match = tk.Frame(nb_tables, bg=BG2)
nb_tables.add(t_match, text="  MATCH  ")

form_m = tk.Frame(t_match, bg=BG2, pady=10, padx=10)
form_m.pack(fill="x")

labels_m = ["ID match", "Date (AAAA-MM-JJ)", "Stade"]
entries_m = []
for i, lbl in enumerate(labels_m):
    make_label(form_m, lbl, 0, i)
    e = make_entry(form_m, 1, i, 18)
    entries_m.append(e)

tree_m_frame, tree_m = make_tree_frame(t_match)
tree_m_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

def refresh_match():
    cols, rows, err = run_query("SELECT * FROM MATCH_F;")
    show_results(tree_m, cols, rows, err)
    tree_m["columns"] = cols or []
    for c in (cols or []):
        tree_m.heading(c, text=c)
        tree_m.column(c, width=150, anchor="w")

def add_match():
    vals = [e.get().strip() for e in entries_m]
    if not all(vals):
        messagebox.showwarning("Champ manquant", "Remplis tous les champs.")
        return
    try:
        cur.execute("INSERT INTO MATCH_F VALUES (?,?,?)",
                    (int(vals[0]), vals[1], vals[2]))
        conn.commit()
        for e in entries_m: e.delete(0, tk.END)
        refresh_match()
    except Exception as ex:
        messagebox.showerror("Erreur", str(ex))

def del_match():
    sel = tree_m.selection()
    if not sel: return
    row = tree_m.item(sel[0])["values"]
    cur.execute("DELETE FROM MATCH_F WHERE id_match=?", (row[0],))
    conn.commit()
    refresh_match()

btn_frame_m = tk.Frame(t_match, bg=BG2, pady=6, padx=10)
btn_frame_m.pack(fill="x")
make_btn(btn_frame_m, "➕  Ajouter", add_match).pack(side="left", padx=(0,8))
make_btn(btn_frame_m, "🗑  Supprimer sélection", del_match, DANGER).pack(side="left")

# ── Table PASSER ────────────────────────────
t_passer = tk.Frame(nb_tables, bg=BG2)
nb_tables.add(t_passer, text="  PASSER  ")

form_p = tk.Frame(t_passer, bg=BG2, pady=10, padx=10)
form_p.pack(fill="x")

labels_p = ["ID passe", "ID match", "ID joueur source", "ID joueur dest", "Minute"]
entries_p = []
for i, lbl in enumerate(labels_p):
    make_label(form_p, lbl, 0, i)
    e = make_entry(form_p, 1, i, 12)
    entries_p.append(e)

tree_p_frame, tree_p = make_tree_frame(t_passer)
tree_p_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

def refresh_passer():
    cols, rows, err = run_query("""
        SELECT P.id_passe, M.stade, J1.nom AS source, J2.nom AS dest, P.minute
        FROM PASSER P
        JOIN MATCH_F M ON M.id_match = P.id_match
        JOIN JOUEUR J1 ON J1.id_joueur = P.id_joueur_source
        JOIN JOUEUR J2 ON J2.id_joueur = P.id_joueur_dest;
    """)
    show_results(tree_p, cols, rows, err)
    for c in (cols or []):
        tree_p.heading(c, text=c)
        tree_p.column(c, width=120, anchor="w")

def add_passer():
    vals = [e.get().strip() for e in entries_p]
    if not all(vals):
        messagebox.showwarning("Champ manquant", "Remplis tous les champs.")
        return
    try:
        cur.execute("INSERT INTO PASSER VALUES (?,?,?,?,?)",
                    tuple(int(v) for v in vals))
        conn.commit()
        for e in entries_p: e.delete(0, tk.END)
        refresh_passer()
    except Exception as ex:
        messagebox.showerror("Erreur", str(ex))

def del_passer():
    sel = tree_p.selection()
    if not sel: return
    row = tree_p.item(sel[0])["values"]
    cur.execute("DELETE FROM PASSER WHERE id_passe=?", (row[0],))
    conn.commit()
    refresh_passer()

btn_frame_p = tk.Frame(t_passer, bg=BG2, pady=6, padx=10)
btn_frame_p.pack(fill="x")
make_btn(btn_frame_p, "➕  Ajouter", add_passer).pack(side="left", padx=(0,8))
make_btn(btn_frame_p, "🗑  Supprimer sélection", del_passer, DANGER).pack(side="left")

# ── Table TIR ───────────────────────────────
t_tir = tk.Frame(nb_tables, bg=BG2)
nb_tables.add(t_tir, text="  TIR  ")

form_t = tk.Frame(t_tir, bg=BG2, pady=10, padx=10)
form_t.pack(fill="x")

labels_t = ["ID tir", "ID joueur", "ID match"]
entries_t = []
for i, lbl in enumerate(labels_t):
    make_label(form_t, lbl, 0, i)
    e = make_entry(form_t, 1, i, 10)
    entries_t.append(e)

cadre_var = tk.IntVar()
but_var   = tk.IntVar()
tk.Label(form_t, text="Cadré", bg=BG2, fg=TEXT2, font=FONT_UI).grid(row=0, column=3, padx=8)
tk.Checkbutton(form_t, variable=cadre_var, bg=BG2, fg=ACCENT2,
               selectcolor=BG3, activebackground=BG2).grid(row=1, column=3, padx=8)
tk.Label(form_t, text="But", bg=BG2, fg=TEXT2, font=FONT_UI).grid(row=0, column=4, padx=8)
tk.Checkbutton(form_t, variable=but_var, bg=BG2, fg=ACCENT2,
               selectcolor=BG3, activebackground=BG2).grid(row=1, column=4, padx=8)

tree_t_frame, tree_t = make_tree_frame(t_tir)
tree_t_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

def refresh_tir():
    cols, rows, err = run_query("""
        SELECT T.id_tir, J.nom AS joueur, M.stade,
               CASE T.cadre WHEN 1 THEN 'oui' ELSE 'non' END AS cadré,
               CASE T.but   WHEN 1 THEN 'oui' ELSE 'non' END AS but
        FROM TIR T
        JOIN JOUEUR J  ON J.id_joueur = T.id_joueur
        JOIN MATCH_F M ON M.id_match  = T.id_match;
    """)
    show_results(tree_t, cols, rows, err)
    for c in (cols or []):
        tree_t.heading(c, text=c)
        tree_t.column(c, width=130, anchor="w")

def add_tir():
    vals = [e.get().strip() for e in entries_t]
    if not all(vals):
        messagebox.showwarning("Champ manquant", "Remplis les champs ID.")
        return
    try:
        cur.execute("INSERT INTO TIR VALUES (?,?,?,?,?)",
                    (int(vals[0]), int(vals[1]), int(vals[2]),
                     cadre_var.get(), but_var.get()))
        conn.commit()
        for e in entries_t: e.delete(0, tk.END)
        cadre_var.set(0); but_var.set(0)
        refresh_tir()
    except Exception as ex:
        messagebox.showerror("Erreur", str(ex))

def del_tir():
    sel = tree_t.selection()
    if not sel: return
    row = tree_t.item(sel[0])["values"]
    cur.execute("DELETE FROM TIR WHERE id_tir=?", (row[0],))
    conn.commit()
    refresh_tir()

btn_frame_t = tk.Frame(t_tir, bg=BG2, pady=6, padx=10)
btn_frame_t.pack(fill="x")
make_btn(btn_frame_t, "➕  Ajouter", add_tir).pack(side="left", padx=(0,8))
make_btn(btn_frame_t, "🗑  Supprimer sélection", del_tir, DANGER).pack(side="left")

# ═══════════════════════════════════════════════
#  ONGLET 2 — Requêtes Partie A
# ═══════════════════════════════════════════════
def make_query_tab(nb_parent, tab_name, query_list):
    frame = tk.Frame(nb_parent, bg=BG)
    nb_parent.add(frame, text=f"  {tab_name}  ")

    paned = tk.PanedWindow(frame, orient="vertical", bg=BG,
                           sashrelief="flat", sashwidth=6)
    paned.pack(fill="both", expand=True, padx=10, pady=10)

    top = tk.Frame(paned, bg=BG2, bd=0)
    paned.add(top, minsize=200)

    # Liste des requêtes
    listbox_frame = tk.Frame(top, bg=BG2)
    listbox_frame.pack(side="left", fill="y", padx=(0,1))
    tk.Label(listbox_frame, text="Requêtes", bg=BG2, fg=ACCENT,
             font=FONT_H, pady=8).pack(fill="x", padx=10)
    lb = tk.Listbox(listbox_frame, bg=BG3, fg=TEXT, font=FONT_UI,
                    selectbackground=ACCENT, selectforeground="#fff",
                    relief="flat", bd=0, width=32,
                    highlightthickness=0, activestyle="none")
    lb.pack(fill="both", expand=True, padx=4, pady=(0,4))
    for q in query_list:
        lb.insert(tk.END, "  " + q[0])

    # Éditeur SQL
    right = tk.Frame(top, bg=BG2)
    right.pack(side="left", fill="both", expand=True)
    tk.Label(right, text="SQL", bg=BG2, fg=ACCENT,
             font=FONT_H, pady=8).pack(anchor="w", padx=10)
    sql_txt = tk.Text(right, bg=BG3, fg="#7dd3fc", insertbackground=TEXT,
                      font=FONT_MONO, relief="flat", bd=0,
                      highlightthickness=1, highlightbackground=BORDER,
                      highlightcolor=ACCENT, height=8)
    sql_txt.pack(fill="both", expand=True, padx=8, pady=(0,8))

    def on_select(evt):
        sel = lb.curselection()
        if not sel: return
        sql_txt.delete("1.0", tk.END)
        sql_txt.insert(tk.END, query_list[sel[0]][1])

    lb.bind("<<ListboxSelect>>", on_select)

    # Panneau résultats
    bottom = tk.Frame(paned, bg=BG)
    paned.add(bottom, minsize=160)

    res_label = tk.Label(bottom, text="Résultats", bg=BG, fg=ACCENT,
                         font=FONT_H, pady=6)
    res_label.pack(anchor="w", padx=10)

    tree_frame, tree = make_tree_frame(bottom)
    tree_frame.pack(fill="both", expand=True)

    def run():
        sql = sql_txt.get("1.0", tk.END).strip()
        if not sql:
            messagebox.showwarning("Vide", "Écris ou sélectionne une requête.")
            return
        cols, rows, err = run_query(sql)
        show_results(tree, cols, rows, err)
        if not err:
            res_label.config(text=f"Résultats  —  {len(rows)} ligne(s)")
            for c in cols:
                tree["columns"] = cols
                tree.heading(c, text=c)
                tree.column(c, width=max(80, 700 // max(len(cols),1)), anchor="w")

    btn_bar = tk.Frame(top, bg=BG2)
    btn_bar.pack(side="right", fill="y", padx=8, pady=10)
    make_btn(btn_bar, "▶️  Exécuter", run, ACCENT2).pack(pady=4)

    return frame

make_query_tab(nb, "⚽ Partie A — Modélisation", QUERIES["Partie A"])
make_query_tab(nb, "📊 Partie B — Agrégats",    QUERIES["Partie B"])

# ═══════════════════════════════════════════════
#  ONGLET 4 — Console SQL libre
# ═══════════════════════════════════════════════
tab_sql = tk.Frame(nb, bg=BG)
nb.add(tab_sql, text="  🖥  Console SQL  ")

tk.Label(tab_sql, text="Console SQL libre", bg=BG, fg=ACCENT,
         font=FONT_H, pady=10).pack(anchor="w", padx=14)

sql_console = tk.Text(tab_sql, bg=BG3, fg="#7dd3fc", insertbackground=TEXT,
                      font=FONT_MONO, height=8, relief="flat",
                      highlightthickness=1, highlightbackground=BORDER,
                      highlightcolor=ACCENT)
sql_console.pack(fill="x", padx=12, pady=(0,8))
sql_console.insert(tk.END, "SELECT * FROM JOUEUR;")

res_console_label = tk.Label(tab_sql, text="Résultats", bg=BG, fg=ACCENT,
                              font=FONT_H, pady=4)
res_console_label.pack(anchor="w", padx=14)

tree_c_frame, tree_c = make_tree_frame(tab_sql)
tree_c_frame.pack(fill="both", expand=True, padx=12, pady=(0,10))

def run_console():
    sql = sql_console.get("1.0", tk.END).strip()
    cols, rows, err = run_query(sql)
    show_results(tree_c, cols, rows, err)
    if not err:
        res_console_label.config(text=f"Résultats  —  {len(rows)} ligne(s)")
        tree_c["columns"] = cols
        for c in cols:
            tree_c.heading(c, text=c)
            tree_c.column(c, width=max(80, 700 // max(len(cols),1)), anchor="w")

btn_console = tk.Frame(tab_sql, bg=BG)
btn_console.pack(fill="x", padx=12, pady=(0,8))
make_btn(btn_console, "▶️  Exécuter (Ctrl+Entrée)", run_console, ACCENT2).pack(side="left")
root.bind("<Control-Return>", lambda e: run_console())

# ── Barre de statut ─────────────────────────
status = tk.Frame(root, bg=BG3, height=28)
status.pack(fill="x", side="bottom")
tk.Label(status, text="✅  Base de données SQLite en mémoire  |  Python 3  |  Tkinter",
         bg=BG3, fg=TEXT2, font=FONT_SM, pady=6).pack(side="left", padx=12)

# Initialisation des vues
refresh_joueur()
refresh_match()
refresh_passer()
refresh_tir()

root.mainloop()
