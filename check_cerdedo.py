
from etl_congreso.db import get_connection

try:
    with get_connection() as conn:
        with conn.cursor() as cur:
            query = "SELECT prov_code, muni_code, nombre FROM municipio WHERE nombre LIKE 'Cerdedo%' LIMIT 5;"
            print(f"Executing: {query}")
            cur.execute(query)
            rows = cur.fetchall()
            print(f"Found {len(rows)} rows:")
            for row in rows:
                print(row)
except Exception as e:
    print(f"Error: {e}")
