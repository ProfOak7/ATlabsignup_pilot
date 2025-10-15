# canvas_client.py
from typing import Any, Dict, List, Optional


class CanvasClient:
def __init__(self, base_url: str, token: str):
# base_url like "https://cuesta.instructure.com"
self.base = base_url.rstrip('/') + '/api/v1'
self.sess = requests.Session()
self.sess.headers.update({"Authorization": f"Bearer {token}"})


# ---------------- Users ----------------
def search_course_users(self, course_id: int, search_term: str, enrollment_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
params: Dict[str, Any] = {"search_term": search_term}
if enrollment_types:
for t in enrollment_types:
params.setdefault("enrollment_type[]", []).append(t)
r = self.sess.get(f"{self.base}/courses/{course_id}/users", params=params)
r.raise_for_status()
return r.json()


def list_course_users(self, course_id: int, enrollment_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
params: Dict[str, Any] = {}
if enrollment_types:
for t in enrollment_types:
params.setdefault("enrollment_type[]", []).append(t)
# Basic pagination (Canvas uses Link headers, but this is fine for modest rosters)
users: List[Dict[str, Any]] = []
url = f"{self.base}/courses/{course_id}/users"
while url:
r = self.sess.get(url, params=params if '?' not in url else None)
r.raise_for_status()
users.extend(r.json())
url = r.links.get('next', {}).get('url')
params = None
return users


# ------------- Custom Gradebook Columns -------------
def list_columns(self, course_id: int):
r = self.sess.get(f"{self.base}/courses/{course_id}/custom_gradebook_columns")
r.raise_for_status()
return r.json()


def create_column(self, course_id: int, title: str, position: int, hidden: bool = False) -> int:
r = self.sess.post(
f"{self.base}/courses/{course_id}/custom_gradebook_columns",
json={"column": {"title": title, "position": position, "hidden": hidden}},
)
r.raise_for_status()
return r.json()["id"]


def write_cell(self, course_id: int, column_id: int, user_id: int, content: str):
r = self.sess.put(
f"{self.base}/courses/{course_id}/custom_gradebook_columns/{column_id}/data/{user_id}",
json={"column_data": {"content": content}},
)
r.raise_for_status()
return r.json()


def read_column_data(self, course_id: int, column_id: int):
# Returns a list of {user_id, content}
r = self.sess.get(f"{self.base}/courses/{course_id}/custom_gradebook_columns/{column_id}/data")
r.raise_for_status()
return r.json()
