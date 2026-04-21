from pathlib import Path
import duckdb


def create_tpch_example_duckdb_db(
    db_path: str | Path,
    scale_factor: float = 1.0,
    overwrite: bool = False,
) -> Path:
    db_path = Path(db_path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if db_path.exists() and not overwrite:
        con = duckdb.connect(str(db_path))
        try:
            table_count = con.execute(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = 'main'"
            ).fetchone()[0]
        finally:
            con.close()

        if table_count > 0:
            return db_path
        else:
            db_path.unlink()

    if db_path.exists() and overwrite:
        db_path.unlink()

    con = duckdb.connect(str(db_path))
    try:
        con.execute("INSTALL tpch")
        con.execute("LOAD tpch")
        con.execute(f"CALL dbgen(sf = {scale_factor})")
    finally:
        con.close()

    return db_path