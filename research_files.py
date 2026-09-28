"""Extract citeable text from uploaded research documents in memory."""

from io import BytesIO
from pathlib import PurePosixPath

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader

from project_files import MAX_FILES, MAX_TOTAL_BYTES, ProjectFile, ProjectInputError

MAX_RESEARCH_BYTES = 10_000_000
MAX_PDF_PAGES = 100
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


def _docx(name: str, data: bytes) -> ProjectFile:
    try:
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
    except Exception as error:
        raise ProjectInputError(f"{name} could not be read as a DOCX document.") from error
    if not output:
        raise ProjectInputError(f"{name} has no readable text.")
    return ProjectFile(name, '\n'.join(output), 'research_docx', tuple(locations), f"{paragraphs} paragraphs, {tables} tables")


def read_research_files(uploads: list) -> tuple[list[ProjectFile], list[str]]:
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
                file = _docx(name, data)
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
