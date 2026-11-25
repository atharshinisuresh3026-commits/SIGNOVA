import streamlit as st

from signova import ui
from signova.state import bump_text, get_db, init_state

init_state()
db = get_db()
ui.page_header("Translation history", "Sentences you saved from the converter, stored only in a local SQLite file.")

search = st.text_input("Search saved translations", placeholder="Type a word to filter", key="hist_search")
entries = db.list(search=search)
total = db.count()

m1, m2, m3 = st.columns([1, 1, 1])
m1.metric("Saved translations", total)
m2.download_button(
    "Export as CSV", disabled=not entries, key="hist_export", mime="text/csv", file_name="signova_history.csv",
    data="id,created_at,word_count,text\n" + "\n".join(
        f'{e.id},{e.created_at},{e.word_count},"{e.text.replace(chr(34), chr(34) * 2)}"' for e in entries),
)
with m3:
    confirm = st.checkbox("Confirm delete all", key="hist_confirm", disabled=total == 0)
    if st.button("Delete all history", disabled=not confirm, key="hist_clear"):
        db.clear()
        st.session_state.hist_confirm = False
        st.rerun()

if not entries:
    st.info("Nothing saved yet." if not search else "No saved translation matches that search.")
    st.stop()

for e in entries:
    with st.container(border=True):
        left, right = st.columns([5, 2])
        left.markdown(f'<div class="sg-hist">{ui.esc(e.text)}</div>'
                      f'<div class="sg-hist-meta">{ui.esc(e.created_at)} &middot; {e.word_count} word(s)</div>',
                      unsafe_allow_html=True)
        b1, b2 = right.columns(2)
        if b1.button("Open", key=f"open_{e.id}", help="Load this text into the converter"):
            st.session_state.buffer.set_text(e.text)
            bump_text()
            st.switch_page("views/converter.py")
        if b2.button("Delete", key=f"del_{e.id}"):
            db.delete(e.id)
            st.rerun()
