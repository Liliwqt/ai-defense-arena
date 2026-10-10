"""Read a small project's text and source files without extracting ZIPs to disk."""

from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile


# Keep the complete accepted project within a bounded AI analysis request.
MAX_FILES = 100
MAX_FILE_BYTES = 200_000
MAX_TOTAL_BYTES = 600_000
MAX_ARCHIVE_BYTES = 25_000_000
MAX_ZIP_ENTRIES = 2_000
ALLOWED_EXTENSIONS = {
    ".md", ".txt", ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".html",
    ".css", ".java", ".go", ".rs", ".sql", ".yaml", ".yml", ".toml", ".sh",
    ".c", ".cpp", ".h", ".hpp", ".kt", ".swift", ".rb", ".php", ".vue", ".svelte",
}
IGNORED_DIRECTORIES = {
    "node_modules", ".venv", "venv", ".git", "__pycache__", "dist", "build",
    "coverage", "target", "__macosx",
}
IGNORED_SECRET_FILES = {
    "credentials.json", "secrets.json", "service-account.json", "service_account.json",
}


@dataclass(frozen=True)
class ProjectFile:
    name: str
    content: str
    kind: str = "source"
    locations: tuple[str, ...] = ()
    detail: str = ""

    def location_for(self, line: int) -> str:
        return self.locations[line - 1] if self.locations else f"Line {line}"


class ProjectInputError(Exception):
    """An upload cannot be included in the project context."""


def _source_path(raw_name: str) -> str | None:
    """Keep safe relative source paths and ignore hidden, generated, or other files."""
    name = raw_name.replace("\\", "/")
    parts = name.split("/")
    if not name or name.startswith("/") or any(part in {"", ".", ".."} for part in parts):
        return None
    if len(parts[0]) >= 2 and parts[0][1] == ":":
        return None
    if any(part.startswith(".") for part in parts):
        return None
    if any(part.lower() in IGNORED_DIRECTORIES for part in parts[:-1]):
        return None
    if parts[-1].lower() in IGNORED_SECRET_FILES:
        return None
    if PurePosixPath(name).suffix.lower() not in ALLOWED_EXTENSIONS:
        return None
    return name


def _read_archive(data: bytes) -> list[ProjectFile]:
    if len(data) > MAX_ARCHIVE_BYTES:
        raise ProjectInputError(f"The ZIP exceeds the {MAX_ARCHIVE_BYTES // 1_000_000} MB compressed size limit.")

    files: list[ProjectFile] = []
    total_bytes = 0
    try:
        with ZipFile(BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ZIP_ENTRIES:
                raise ProjectInputError("The ZIP has too many entries.")
            for entry in entries:
                if entry.is_dir():
                    continue
                name = _source_path(entry.filename)
                if name is None:
                    continue
                if entry.file_size > MAX_FILE_BYTES:
                    raise ProjectInputError(f"{name} exceeds the {MAX_FILE_BYTES // 1_000} KB per-file limit.")
                if len(files) >= MAX_FILES:
                    raise ProjectInputError(f"Include at most {MAX_FILES} source files.")
                if total_bytes + entry.file_size > MAX_TOTAL_BYTES:
                    raise ProjectInputError(f"Project text exceeds the {MAX_TOTAL_BYTES // 1_000} KB total limit.")
                with archive.open(entry) as member:
                    content_bytes = member.read(MAX_FILE_BYTES + 1)
                if len(content_bytes) > MAX_FILE_BYTES:
                    raise ProjectInputError(f"{name} exceeds the {MAX_FILE_BYTES // 1_000} KB per-file limit.")
                try:
                    content = content_bytes.decode("utf-8")
                except UnicodeDecodeError as error:
                    raise ProjectInputError(f"{name} is not UTF-8 text.") from error
                total_bytes += len(content_bytes)
                files.append(ProjectFile(name, content))
    except (BadZipFile, NotImplementedError, RuntimeError, OSError) as error:
        raise ProjectInputError("The ZIP is invalid or cannot be read.") from error
    return files


def read_project_files(uploads: list) -> tuple[list[ProjectFile], list[str]]:
    """Read all accepted project text or return a clear validation error."""
    files: list[ProjectFile] = []
    seen_names: set[str] = set()
    total_bytes = 0

    for upload in uploads:
        raw = upload.getvalue()
        if upload.name.lower().endswith(".zip"):
            try:
                candidates = _read_archive(raw)
            except ProjectInputError as error:
                return [], [str(error)]
        else:
            name = _source_path(upload.name)
            if name is None:
                return [], [f"Unsupported or unsafe source file: {upload.name}"]
            if len(raw) > MAX_FILE_BYTES:
                return [], [f"{name} exceeds the {MAX_FILE_BYTES // 1_000} KB per-file limit."]
            try:
                content = raw.decode("utf-8")
            except UnicodeDecodeError:
                return [], [f"{name} is not UTF-8 text."]
            candidates = [ProjectFile(name, content)]

        for file in candidates:
            if file.name in seen_names:
                return [], [f"Duplicate filename: {file.name}"]
            if len(files) >= MAX_FILES:
                return [], [f"Include at most {MAX_FILES} source files."]
            file_bytes = len(file.content.encode("utf-8"))
            if total_bytes + file_bytes > MAX_TOTAL_BYTES:
                return [], [f"Project text exceeds the {MAX_TOTAL_BYTES // 1_000} KB total limit."]
            seen_names.add(file.name)
            total_bytes += file_bytes
            files.append(file)

    if not files:
        return [], ["No supported UTF-8 source or documentation files were found."]
    return sorted(files, key=lambda file: file.name.lower()), []
