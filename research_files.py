"""Extract citeable text from uploaded research documents in memory."""

from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import time
from zipfile import ZipFile

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader

from project_files import MAX_FILES, MAX_TOTAL_BYTES, ProjectFile, ProjectInputError

MAX_RESEARCH_BYTES = 10_000_000
MAX_PDF_PAGES = 100
MAX_DOCX_ENTRIES = 512
MAX_DOCX_MEMBER_BYTES = 8_000_000
MAX_DOCX_EXPANDED_BYTES = 32_000_000
MAX_DOCX_RATIO = 1000
DOCX_PARSE_SECONDS = 20
MAX_DOCX_RESULT_BYTES = 4_000_000
RESEARCH_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def _safe_name(name: str) -> str:
    path = PurePosixPath(name.replace('\\', '/'))
    if not name or path.is_absolute() or len(path.parts) != 1 or name.startswith('.') or path.suffix.lower() not in RESEARCH_EXTENSIONS:
        raise ProjectInputError(f"Unsupported research document: {name}")
    return name


def _lines(text: str, label: str, output: list[str], locations: list[str]) -> None:
    for number, raw in enumerate(text.splitlines(), 1):
        if raw.strip():
            output.append(raw)
            locations.append(f"{label} · extracted line {number}" if label.startswith('Page ') else label)


def _pdf(name: str, data: bytes) -> ProjectFile:
    try:
        reader = PdfReader(BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise ProjectInputError(f"{name} is encrypted. Upload an unlocked, text-based PDF.")
        if len(reader.pages) > MAX_PDF_PAGES:
            raise ProjectInputError(f"{name} exceeds the {MAX_PDF_PAGES}-page PDF limit.")
        output: list[str] = []
        locations: list[str] = []
        for page_number, page in enumerate(reader.pages, 1):
            before = len(output)
            _lines(page.extract_text() or '', f"Page {page_number}", output, locations)
            if len(output) == before:
                raise ProjectInputError(
                    f"{name}, page {page_number} has no readable text. Upload a text-based PDF or a text copy."
                )
    except ProjectInputError:
        raise
    except Exception as error:
        raise ProjectInputError(f"{name} could not be read as a PDF.") from error
    if not output:
        raise ProjectInputError(f"{name} has no readable text.")
    return ProjectFile(name, '\n'.join(output), 'research_pdf', tuple(locations), f"{len(reader.pages)} page{'s' if len(reader.pages) != 1 else ''}")


def _validate_docx_package(name: str, data: bytes, cancel=None) -> None:
    """Check every member, including parts that never appear in extracted text.

    This runs inside the limited worker; even central-directory parsing is isolated.
    """
    total = 0
    with ZipFile(BytesIO(data)) as archive:
        entries = archive.infolist()
        if len(entries) > MAX_DOCX_ENTRIES:
            raise ProjectInputError(f'{name} has too many DOCX package entries.')
        names = set()
        for entry in entries:
            if entry.filename in names or entry.flag_bits & 1:
                raise ProjectInputError(f'{name} has duplicate or encrypted DOCX parts.')
            names.add(entry.filename)
            if (entry.file_size > MAX_DOCX_MEMBER_BYTES
                    or entry.file_size > MAX_DOCX_RATIO * max(1, entry.compress_size)
                    or total + entry.file_size > MAX_DOCX_EXPANDED_BYTES):
                raise ProjectInputError(f'{name} exceeds the expanded DOCX package limits.')
            actual = 0
            with archive.open(entry) as member:
                while True:
                    if cancel is not None and cancel.is_set():
                        raise ProjectInputError('Document processing was cancelled.')
                    chunk = member.read(min(65536, MAX_DOCX_MEMBER_BYTES - actual + 1))
                    if not chunk:
                        break
                    actual += len(chunk)
                    total += len(chunk)
                    if actual > MAX_DOCX_MEMBER_BYTES or total > MAX_DOCX_EXPANDED_BYTES:
                        raise ProjectInputError(f'{name} exceeds the expanded DOCX package limits.')
            if actual != entry.file_size:
                raise ProjectInputError(f'{name} has inconsistent DOCX package sizes.')


def _docx_in_process(name: str, data: bytes) -> ProjectFile:
    """Worker-only loader, after bounded package admission."""
    try:
        _validate_docx_package(name, data)
        document = Document(BytesIO(data))
        output: list[str] = []
        locations: list[str] = []
        paragraphs = tables = 0
        for child in document.element.body.iterchildren():
            if child.tag == qn('w:p'):
                paragraphs += 1
                _lines(Paragraph(child, document).text, f"Paragraph {paragraphs}", output, locations)
            elif child.tag == qn('w:tbl'):
                tables += 1
                table = Table(child, document)
                for row_number, row in enumerate(table.rows, 1):
                    for cell_number, cell in enumerate(row.cells, 1):
                        _lines(cell.text, f"Table {tables}, row {row_number}, cell {cell_number}", output, locations)
    except ProjectInputError:
        raise
    except Exception as error:
        raise ProjectInputError(f"{name} could not be read as a DOCX document.") from error
    if not output:
        raise ProjectInputError(f"{name} has no readable text.")
    return ProjectFile(name, '\n'.join(output), 'research_docx', tuple(locations), f"{paragraphs} paragraphs, {tables} tables")


def _docx(name: str, data: bytes, cancel=None) -> ProjectFile:
    """No document parser or expanded archive allocation runs in the room process."""
    if sys.platform != 'linux':
        raise ProjectInputError('Secure DOCX processing requires a Linux server. Upload a TXT or Markdown copy instead.')
    worker = Path(__file__).with_name('document_parser_worker.py').resolve()
    process = None
    try:
        if cancel is not None and cancel.is_set():
            raise ProjectInputError('Document processing was cancelled.')
        # No account, provider, database, voucher or AI credentials enter the child.
        process = subprocess.Popen([sys.executable, '-I', str(worker)], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                   env={'LANG': 'C.UTF-8'}, cwd=worker.parent)
        deadline = time.monotonic() + DOCX_PARSE_SECONDS
        pending = data
        while True:
            if cancel is not None and cancel.is_set():
                raise ProjectInputError('Document processing was cancelled.')
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ProjectInputError(f'{name} took too long to process. Upload a simpler document.')
            try:
                output, _ = process.communicate(pending, timeout=min(.1, remaining))
                break
            except subprocess.TimeoutExpired:
                pending = None
        if process.returncode or len(output) > MAX_DOCX_RESULT_BYTES:
            raise ProjectInputError(f'{name} exceeded safe document-processing limits or could not be read.')
        result = json.loads(output)
        if 'error' in result:
            raise ProjectInputError(result['error'].replace('document.docx', name))
        return ProjectFile(name, result['content'], 'research_docx', tuple(result['locations']), result['detail'])
    except ProjectInputError:
        raise
    except (OSError, ValueError, KeyError) as error:
        raise ProjectInputError(f'{name} could not be read as a DOCX document.') from error
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.communicate()  # Reap it before the parser slot can be released.


def read_research_files(uploads: list, *, cancel=None) -> tuple[list[ProjectFile], list[str]]:
    """Return extracted research text or a user-safe validation error."""
    try:
        if not uploads:
            raise ProjectInputError('Upload at least one research document.')
        if len(uploads) > MAX_FILES:
            raise ProjectInputError(f"Include at most {MAX_FILES} files.")
        files: list[ProjectFile] = []
        seen: set[str] = set()
        total = 0
        for upload in uploads:
            if cancel is not None and cancel.is_set():
                raise ProjectInputError('Document processing was cancelled.')
            name = _safe_name(upload.name)
            if name.lower() in seen:
                raise ProjectInputError(f"Duplicate filename: {name}")
            seen.add(name.lower())
            data = upload.getvalue()
            if len(data) > MAX_RESEARCH_BYTES:
                raise ProjectInputError(f"{name} exceeds the 10 MB research-document limit.")
            suffix = PurePosixPath(name).suffix.lower()
            if suffix == '.pdf':
                file = _pdf(name, data)
            elif suffix == '.docx':
                file = _docx(name, data, cancel)
            else:
                try:
                    content = data.decode('utf-8')
                except UnicodeDecodeError as error:
                    raise ProjectInputError(f"{name} is not UTF-8 text.") from error
                if not content.strip():
                    raise ProjectInputError(f"{name} has no readable text.")
                file = ProjectFile(name, content, 'research_text', detail=f"{len(content.splitlines())} lines")
            total += len(file.content.encode('utf-8'))
            if total > MAX_TOTAL_BYTES:
                raise ProjectInputError(f"Research text exceeds the {MAX_TOTAL_BYTES // 1_000} KB analysis limit.")
            files.append(file)
        return files, []
    except ProjectInputError as error:
        return [], [str(error)]


def combine_sources(sources: list[ProjectFile], research: list[ProjectFile]) -> tuple[list[ProjectFile], list[str]]:
    files = sources + research
    if len(files) > MAX_FILES:
        return [], [f"Include at most {MAX_FILES} source and research files combined."]
    names = [file.name.lower() for file in files]
    if len(names) != len(set(names)):
        return [], ['Project and research filenames must be unique.']
    if sum(len(file.content.encode('utf-8')) for file in files) > MAX_TOTAL_BYTES:
        return [], [f"Combined project and research text exceeds the {MAX_TOTAL_BYTES // 1_000} KB analysis limit."]
    return files, []
