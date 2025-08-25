import io
import os
import csv
import json
import unittest
import tempfile
from contextlib import redirect_stdout

# Import the functions from your script
# Make sure the project root (containing json_to_csv.py) is on PYTHONPATH when running tests.
import json_to_csv  # noqa: E402


def _read_csv(path, delimiter=","):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


class JsonToCsvTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def _write_json(self, name, obj):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
        return path

    def test_dict_of_dicts_basic(self):
        data = {
            "1": {"name": "Alice", "role": "Admin"},
            "2": {"name": "Bob", "role": "User"},
        }
        jpath = self._write_json("data.json", data)
        out = json_to_csv.json_to_csv(jpath)  # default <input>.csv
        rows = _read_csv(out)
        self.assertEqual(rows, [
            {"id": "1", "name": "Alice", "role": "Admin"},
            {"id": "2", "name": "Bob",   "role": "User"},
        ])

    def test_list_of_dicts_infer_fields(self):
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "role": "User", "name": "Bob"},  # order/union test
        ]
        jpath = self._write_json("list.json", data)
        out = json_to_csv.json_to_csv(jpath)
        rows = _read_csv(out)
        # Field inference should preserve first-seen order: id, name, role
        self.assertEqual(rows, [
            {"id": "1", "name": "Alice", "role": ""},
            {"id": "2", "name": "Bob",   "role": "User"},
        ])

    def test_fields_override_and_ignore_extras(self):
        data = [
            {"id": 1, "name": "Alice", "role": "Admin", "extra": "x"},
        ]
        jpath = self._write_json("override.json", data)
        out = json_to_csv.json_to_csv(jpath, fields=["name", "id"])  # enforce order + drop others
        rows = _read_csv(out)
        self.assertEqual(rows, [{"name": "Alice", "id": "1"}])

    def test_delimiter_semicolon(self):
        data = [{"id": 1, "name": "Alice"}]
        jpath = self._write_json("semi.json", data)
        out = json_to_csv.json_to_csv(jpath, delimiter=";")
        rows = _read_csv(out, delimiter=";")
        self.assertEqual(rows, [{"id": "1", "name": "Alice"}])

    def test_cli_prints_output_and_returns_zero(self):
        data = [{"id": 1, "name": "Alice"}]
        jpath = self._write_json("cli.json", data)
        expected_csv = os.path.splitext(jpath)[0] + ".csv"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = json_to_csv.main([jpath])
        printed = buf.getvalue().strip()

        self.assertEqual(code, 0)
        self.assertEqual(printed, expected_csv)
        self.assertTrue(os.path.exists(expected_csv))

    def test_invalid_json_exit_code_2(self):
        # Write malformed JSON
        jpath = os.path.join(self.dir, "bad.json")
        with open(jpath, "w", encoding="utf-8") as f:
            f.write('{"id": 1,,,,}')

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = json_to_csv.main([jpath])
        self.assertEqual(code, 2)

    def test_bad_top_level_type_exit_code_2(self):
        jpath = os.path.join(self.dir, "num.json")
        with open(jpath, "w", encoding="utf-8") as f:
            f.write("42")

        code = json_to_csv.main([jpath])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
