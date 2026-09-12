import sqlite3
import pandas as pd
import streamlit as st

# Configurazione pagina e grafica
st.set_page_config(page_title="Magazzino Ricambi Auto", layout="wide")

# CSS per ingrandire i bottoni e i testi per renderli facilissimi da leggere
st.markdown(
    """
    <style>
    div.stButton > button {
        font-size: 20px !important;
        font-weight: bold !important;
        padding: 10px 24px !important;
        border-radius: 8px !important;
    }
    .stTextInput input {
        font-size: 20px !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Connessione al Database SQLite (crea il file 'magazzino.db' in automatico)
conn = sqlite3.connect("magazzino.db", check_same_thread=False)
c = conn.cursor()

c.execute(
    """CREATE TABLE IF NOT EXISTS pezzi 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              nome TEXT, 
              posizione TEXT, 
              quantita INTEGER, 
              note TEXT, 
              eliminato INTEGER DEFAULT 0)"""
)
conn.commit()

# Intestazione Principale
st.title("📦 MAGAZZINO RICAMBI AUTO")

# Menu principale a schede grandi in alto
scelta = st.radio(
    "SCEGLI COSA FARE:",
    ["🔍 CERCA PEZZI", "➕ AGGIUNGI NUOVO PEZZO", "🗑️ CESTINO / RECUPERO"],
    horizontal=True,
)

st.divider()

# ---------------------------------------------------------
# SCHEDA 1: CERCA E GESTISCI PEZZI
# ---------------------------------------------------------
if scelta == "🔍 CERCA PEZZI":
    st.header("🔍 Cerca Pezzo nel Magazzino")

    ricerca = st.text_input("Scrivi qui cosa stai cercando (es. Alternatore, Scaffale A, Opel...):", "")

    query = "SELECT id, nome, posizione, quantita, note FROM pezzi WHERE eliminato = 0"
    if ricerca:
        query += f" AND (nome LIKE '%{ricerca}%' OR posizione LIKE '%{ricerca}%' OR note LIKE '%{ricerca}%')"

    df = pd.read_sql_query(query, conn)

    if df.empty:
        st.info("Nessun pezzo trovato in magazzino.")
    else:
        for idx, row in df.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 3, 2])

                col1.markdown(f"### 🛠️ {row['nome']}")
                col2.markdown(f"📍 **Posizione:**\n### {row['posizione']}")
                col3.markdown(f"🔢 **Qtà:**\n### {row['quantita']}")
                col4.markdown(f"📝 **Note:**\n{row['note']}")

                # Tasto per eliminare
                if col5.button("❌ ELIMINA", key=f"del_{row['id']}"):
                    st.session_state[f"confirm_{row['id']}"] = True

                # POPUP DI SICUREZZA
                if st.session_state.get(f"confirm_{row['id']}", False):
                    st.error(f"⚠️ SICURO DI VOLER CANCELLARE '{row['nome']}'?")
                    c1, c2 = st.columns(2)

                    if c1.button("✔️ SÌ, SPOSTA NEL CESTINO", key=f"yes_{row['id']}"):
                        c.execute("UPDATE pezzi SET eliminato = 1 WHERE id = ?", (row["id"],))
                        conn.commit()
                        st.session_state[f"confirm_{row['id']}"] = False
                        st.rerun()

                    if c2.button("❌ ANNULLA", key=f"no_{row['id']}"):
                        st.session_state[f"confirm_{row['id']}"] = False
                        st.rerun()

                st.divider()

# ---------------------------------------------------------
# SCHEDA 2: AGGIUNGI NUOVO PEZZO
# ---------------------------------------------------------
elif scelta == "➕ AGGIUNGI NUOVO PEZZO":
    st.header("➕ Aggiungi un nuovo pezzo")

    with st.form("form_aggiungi", clear_on_submit=True):
        nome = st.text_input("NOME DEL PEZZO (es. Alternatore Opel Ascona)")
        posizione = st.text_input("DOVE SI TROVA? (es. Scaffale A - Scatola 3)")
        quantita = st.number_input("QUANTI CE NE SONO?", min_value=1, value=1, step=1)
        note = st.text_area("NOTE / COMPATIBILITÀ (es. Motore 1.3S/1.6, revisionato)")

        salva = st.form_submit_button("💾 SALVA IN MAGAZZINO")

        if salva:
            if nome and posizione:
                c.execute(
                    "INSERT INTO pezzi (nome, posizione, quantita, note) VALUES (?, ?, ?, ?)",
                    (nome, posizione, quantita, note),
                )
                conn.commit()
                st.success(f"✅ CONFERMATO: '{nome}' salvato con successo!")
            else:
                st.warning("⚠️ DEVI SCRIVERE ALMENO IL NOME E LA POSIZIONE!")

# ---------------------------------------------------------
# SCHEDA 3: CESTINO E RECUPERO
# ---------------------------------------------------------
elif scelta == "🗑️ CESTINO / RECUPERO":
    st.header("🗑️ Pezzi Eliminati (Cestino)")
    st.write("Qui trovi i pezzi cancellati per errore. Puoi ripristinarli quando vuoi.")

    df_cestino = pd.read_sql_query(
        "SELECT id, nome, posizione, quantita, note FROM pezzi WHERE eliminato = 1", conn
    )

    if df_cestino.empty:
        st.info("Il cestino è completamente vuoto.")
    else:
        for idx, row in df_cestino.iterrows():
            c1, c2, c3 = st.columns([4, 2, 2])
            c1.markdown(f"**{row['nome']}** — Posizione: *{row['posizione']}*")

            if c2.button("♻️ RIPRISTINA PEZZO", key=f"rest_{row['id']}"):
                c.execute("UPDATE pezzi SET eliminato = 0 WHERE id = ?", (row["id"],))
                conn.commit()
                st.rerun()

            if c3.button("🔥 ELIMINA PER SEMPRE", key=f"perm_{row['id']}"):
                c.execute("DELETE FROM pezzi WHERE id = ?", (row["id"],))
                conn.commit()
                st.rerun()

            st.divider()

# ---------------------------------------------------------
# BACKUP FACILE IN FONDO ALLA PAGINA
# ---------------------------------------------------------
st.sidebar.title("💾 Backup")
df_backup = pd.read_sql_query("SELECT * FROM pezzi", conn)
st.sidebar.download_button(
    label="📥 SCARICA BACKUP (CSV)",
    data=df_backup.to_csv(index=False),
    file_name="backup_magazzino_ricambi.csv",
    mime="text/csv",
)
