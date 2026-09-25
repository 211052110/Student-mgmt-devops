import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    os.environ["SMS_DB_PATH"] = db_path

    import importlib
    import main as app_module
    importlib.reload(app_module)  # pick up the temp DB path
    app_module.init_db()

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(db_path)


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_metrics(client):
    res = client.get("/metrics")
    assert res.status_code == 200
    assert b"app_requests_total" in res.data


def test_create_and_list_student(client):
    res = client.post("/students", json={"name": "Aarav Sharma", "roll_number": "21CS101"})
    assert res.status_code == 201
    student_id = res.get_json()["id"]

    res = client.get("/students")
    assert res.status_code == 200
    students = res.get_json()
    assert any(s["id"] == student_id for s in students)


def test_create_student_missing_fields(client):
    res = client.post("/students", json={"name": "No Roll"})
    assert res.status_code == 400


def test_get_single_student(client):
    res = client.post("/students", json={"name": "Priya Verma", "roll_number": "21CS102"})
    student_id = res.get_json()["id"]

    res = client.get(f"/students/{student_id}")
    assert res.status_code == 200
    assert res.get_json()["name"] == "Priya Verma"


def test_get_student_not_found(client):
    res = client.get("/students/9999")
    assert res.status_code == 404


def test_update_student(client):
    res = client.post("/students", json={"name": "Rahul Jain", "roll_number": "21CS103"})
    student_id = res.get_json()["id"]

    res = client.put(f"/students/{student_id}", json={"branch": "CSE"})
    assert res.status_code == 200

    res = client.get(f"/students/{student_id}")
    assert res.get_json()["branch"] == "CSE"


def test_delete_student(client):
    res = client.post("/students", json={"name": "Sana Khan", "roll_number": "21CS104"})
    student_id = res.get_json()["id"]

    res = client.delete(f"/students/{student_id}")
    assert res.status_code == 200

    res = client.get(f"/students/{student_id}")
    assert res.status_code == 404
