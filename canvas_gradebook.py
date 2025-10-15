# canvas_gradebook.py
def ensure_columns(client: CanvasClient, course_id: int, exam_titles: List[str], dsps_title: str) -> ColumnMap:
"""Create missing columns; return title->id map."""
existing = {c["title"]: c for c in client.list_columns(course_id)}
# Compute positions: keep existing positions, append new at end
next_pos = 1 + max([c.get("position", 0) for c in existing.values()] + [0])


ids: Dict[str, int] = {}


def _get_or_create(title: str, hidden: bool) -> int:
if title in existing:
return existing[title]["id"]
nonlocal next_pos
cid = client.create_column(course_id, title=title, position=next_pos, hidden=hidden)
next_pos += 1
return cid


for t in exam_titles:
ids[t] = _get_or_create(t, hidden=False)
ids[dsps_title] = _get_or_create(dsps_title, hidden=True)


return ColumnMap(ids=ids)




def roster_with_columns(client: CanvasClient, course_id: int, colmap: ColumnMap) -> List[Dict[str, Any]]:
"""Return a simple list of dicts: {user_id, name, sis_login_id?, email?, col_values:{title:value}}"""
users = client.list_course_users(course_id, enrollment_types=["student"])
# Build a map of column data per column
per_col: Dict[str, Dict[int, str]] = {}
for title, cid in colmap.ids.items():
data = client.read_column_data(course_id, cid)
per_col[title] = {row.get("user_id"): row.get("content", "") for row in data}


rows: List[Dict[str, Any]] = []
for u in users:
uid = u["id"]
name = u.get("sortable_name") or u.get("name")
email = (u.get("login_id") or "")
row = {
"user_id": uid,
"name": name,
"email": email,
"col_values": {title: per_col.get(title, {}).get(uid, "") for title in colmap.ids.keys()},
}
rows.append(row)
return rows




def record_signup(client: CanvasClient, course_id: int, colmap: ColumnMap, *,
student_search: str, exam_title: str, slot_text: str,
dsps_note: str | None = None) -> Tuple[int, int]:
"""Find the student in the course and write to the target columns.
Returns (user_id, column_id) for the main write.
"""
# Find student by email/login or name (prefer exact login/email when possible)
matches = client.search_course_users(course_id, student_search, enrollment_types=["student"])
if not matches:
raise ValueError(f"No enrolled student matching: {student_search}")
student = matches[0] # TODO: add disambiguation if needed
user_id = student["id"]


# Write main exam cell
column_id = colmap.ids[exam_title]
client.write_cell(course_id, column_id, user_id, slot_text)


# Optionally mirror DSPS
if dsps_note:
dsps_col = colmap.ids.get("DSPS / Notes")
if dsps_col:
client.write_cell(course_id, dsps_col, user_id, dsps_note)


return user_id, column_id
