"""Checks for complete, bounded project uploads."""

import unittest
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from project_files import read_project_files


class Upload:
    def __init__(self, name: str, data: bytes):
        self.name = name
        self.data = data

    def getvalue(self) -> bytes:
        return self.data


def project_zip(entries: dict[str, bytes]) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return output.getvalue()


class ProjectFileTests(unittest.TestCase):
    def test_zip_reads_code_and_docs_with_paths(self):
        archive = project_zip({
            "project/README.md": b"# Queue\n",
            "project/src/queue.py": b"DB = 'queue.db'\n",
            "project/logo.png": b"\x89PNG",
            "project/node_modules/vendor.py": b"ignored\n",
            "project/.env": b"ignored\n",
            "project/credentials.json": b"ignored\n",
        })
        files, errors = read_project_files([Upload("project.zip", archive)])
        self.assertEqual(errors, [])
        self.assertEqual(
            [file.name for file in files],
            ["project/README.md", "project/src/queue.py"],
        )

    def test_loose_files_are_all_read(self):
        files, errors = read_project_files([
            Upload("README.md", b"# Queue\n"),
            Upload("src/queue.py", b"DB = 'queue.db'\n"),
        ])
        self.assertEqual(errors, [])
        self.assertEqual(len(files), 2)
        self.assertEqual(files[1].name, "src/queue.py")

    def test_invalid_zip_is_rejected(self):
        files, errors = read_project_files([Upload("project.zip", b"not a ZIP")])
        self.assertEqual(files, [])
        self.assertIn("invalid", errors[0])

    def test_oversized_source_rejects_whole_zip(self):
        archive = project_zip({
            "README.md": b"# Queue\n",
            "src/large.py": b"x" * 100_001,
        })
        files, errors = read_project_files([Upload("project.zip", archive)])
        self.assertEqual(files, [])
        self.assertIn("100 KB", errors[0])

    def test_total_text_limit_rejects_whole_zip(self):
        archive = project_zip({
            f"src/module_{number}.py": b"x" * 80_000
            for number in range(4)
        })
        files, errors = read_project_files([Upload("project.zip", archive)])
        self.assertEqual(files, [])
        self.assertIn("300 KB", errors[0])

    def test_too_many_source_files_rejects_whole_zip(self):
        archive = project_zip({
            f"src/module_{number}.py": b"pass\n"
            for number in range(61)
        })
        files, errors = read_project_files([Upload("project.zip", archive)])
        self.assertEqual(files, [])
        self.assertIn("60", errors[0])

    def test_unsafe_paths_are_ignored(self):
        archive = project_zip({
            "../outside.py": b"not included\n",
            "README.md": b"# Queue\n",
        })
        files, errors = read_project_files([Upload("project.zip", archive)])
        self.assertEqual(errors, [])
        self.assertEqual([file.name for file in files], ["README.md"])

    def test_duplicate_filename_rejects_project(self):
        files, errors = read_project_files([
            Upload("README.md", b"first\n"),
            Upload("README.md", b"second\n"),
        ])
        self.assertEqual(files, [])
        self.assertIn("Duplicate", errors[0])

    def test_non_utf8_source_rejects_project(self):
        files, errors = read_project_files([Upload("README.md", b"\xff")])
        self.assertEqual(files, [])
        self.assertIn("UTF-8", errors[0])


if __name__ == "__main__":
    unittest.main()
