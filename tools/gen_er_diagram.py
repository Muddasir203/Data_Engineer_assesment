import os
import sqlite3
from contextlib import closing

def generate_mermaid(db_path: str) -> str:
    with closing(sqlite3.connect(db_path)) as conn:
        cur = conn.cursor()
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';").fetchall()]
        cols = {}
        fks = []
        for t in tables:
            cols[t] = cur.execute(f"PRAGMA table_info({t})").fetchall()
            for fk in cur.execute(f"PRAGMA foreign_key_list({t})").fetchall():
                fks.append((t, fk[3], fk[2], fk[4]))  # (from_table, from_col, to_table, to_col)
    
    lines = ["erDiagram"]
    
    # Define tables in specific order to match the required format
    table_order = ["agency", "complaint_type", "descriptor", "borough", "service_requests"]
    
    for t in table_order:
        if t in cols:
            lines.append(f"  {t} {{")
            for _, name, ctype, notnull, dflt, pk in cols[t]:
                # Convert SQLite types to the required format
                if ctype.upper() == "INTEGER":
                    type_str = "INTEGER"
                elif ctype.upper() == "TEXT":
                    type_str = "TEXT"
                elif ctype.upper() == "REAL":
                    type_str = "REAL"
                else:
                    type_str = ctype.upper()
                lines.append(f"    {type_str} {name}")
            lines.append("  }")
    
    # Add foreign key relationships in the specified format
    for ft, fc, tt, tc in fks:
        lines.append(f"  {ft} }}o--|| {tt} : \"FK {fc} → {tc}\"")
    
    return "\n".join(lines)

if __name__ == "__main__":
    db_path = os.getenv("DB_PATH", os.path.join(os.getcwd(), "nyc311.sqlite"))
    mermaid = generate_mermaid(db_path)
    out = os.path.join(os.getcwd(), "outputs", "schema.mmd")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(mermaid)
    print(f"Wrote {out}")
    print("\nGenerated ER Diagram:")
    print(mermaid)
