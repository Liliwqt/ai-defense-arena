"""Private, bounded original PDFs with a lifetime owned by their room."""

from dataclasses import dataclass
import os
from pathlib import Path
import re
import secrets
import shutil
import threading

from fastapi import HTTPException
from backend.resource_limits import limit

REPOSITORY = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class OriginalPDF:
    id: str
    filename: str
    page_count: int

    def snapshot(self):
        return {'id': self.id, 'filename': self.filename, 'page_count': self.page_count}


class RoomDocuments:
    """One creation reservation, retained until its room releases it."""

    def __init__(self, store, size):
        self._store = store
        self._size = size
        self._directory = store.directory / secrets.token_hex(24)
        self._released = False
        self.documents: tuple[OriginalPDF, ...] = ()

    def stage(self, files, uploads):
        # The parser may outlive a cancelled HTTP request. Release and stage
        # share ownership so its late result cannot recreate orphaned files.
        with self._store.lock:
            if self._released:
                raise HTTPException(408, 'Room creation expired. Please retry.')
            pdfs = {file.name: file for file in files if file.kind == 'research_pdf'}
            if not pdfs:
                return
            self._directory.mkdir(mode=0o700)
            documents = []
            for upload in uploads:
                file = pdfs.get(upload.name)
                if file is None:
                    continue
                pages = [int(match[1]) for location in file.locations
                         if (match := re.match(r'^Page (\d+) · extracted line \d+$', location))]
                document = OriginalPDF(secrets.token_hex(24), file.name, max(pages))
                path = self._directory / document.id
                with path.open('xb') as stream:
                    os.chmod(path, 0o600)
                    stream.write(upload.data)
                documents.append(document)
            self.documents = tuple(documents)

    def snapshot(self):
        return [document.snapshot() for document in self.documents]

    def citation(self, filename, location):
        document = next((item for item in self.documents if item.filename == filename), None)
        page = re.match(r'^Page (\d+) · extracted line \d+$', location or '')
        if document and page and 1 <= int(page[1]) <= document.page_count:
            return {'evidence_document_id': document.id, 'evidence_page': int(page[1])}
        return {}

    def open(self, document_id):
        with self._store.lock:
            if self._released or not any(item.id == document_id for item in self.documents):
                raise HTTPException(404, 'Paper unavailable. Rejoin or create a fresh room.')
            try:
                stream = (self._directory / document_id).open('rb')
            except OSError:
                raise HTTPException(404, 'Paper unavailable. Rejoin or create a fresh room.') from None
            return stream

    def release(self):
        with self._store.lock:
            if self._released:
                return
            if self._directory.exists():
                shutil.rmtree(self._directory)
            self._released = True
            self.documents = ()
            self._store.used -= self._size
            self._store.reservations.discard(self)


class DocumentStore:
    """Exclusive process storage; startup cleanup cannot race a live predecessor."""

    def __init__(self):
        directory = Path(os.getenv('ROOM_DOCUMENT_DIR', str(REPOSITORY / '.local' / 'room-pdfs')))
        self.directory = directory if directory.is_absolute() else REPOSITORY / directory
        self.per_room = limit('ROOM_DOCUMENT_BYTES', 110_000_000, 5_000_000_000)
        self.maximum = limit('ROOM_DOCUMENT_TOTAL_BYTES', 500_000_000, 5_000_000_000)
        self.lock = threading.RLock()
        self.used = 0
        self.reservations = set()
        self._lease = None

    def start(self):
        if self._lease is not None:
            return
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.directory, 0o700)
        lease = (self.directory / '.owner').open('a+b')
        try:
            if os.name == 'nt':
                import msvcrt
                lease.seek(0)
                if lease.read(1) == b'':
                    lease.write(b'0'); lease.flush()
                lease.seek(0)
                msvcrt.locking(lease.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            lease.close()
            raise RuntimeError('Another service owns the private paper storage.') from None
        try:
            for path in self.directory.iterdir():
                if re.fullmatch(r'[a-f0-9]{48}', path.name) and path.is_dir() and not path.is_symlink():
                    shutil.rmtree(path)
        except BaseException:
            lease.close()
            raise
        self._lease = lease

    def reserve(self, uploads):
        size = sum(len(upload.data) for upload in uploads if upload.name.lower().endswith('.pdf'))
        with self.lock:
            if self._lease is None:
                raise HTTPException(503, 'Paper storage is restarting. Retry shortly.')
            if size > self.per_room:
                raise HTTPException(413, 'Original PDFs exceed this room\'s storage limit.')
            if self.used + size > self.maximum:
                raise HTTPException(503, 'Paper storage is full. Close an unused room or retry later.')
            reservation = RoomDocuments(self, size)
            self.used += size
            self.reservations.add(reservation)
            return reservation

    def close(self):
        with self.lock:
            for reservation in tuple(self.reservations):
                reservation.release()
            if self._lease is not None:
                self._lease.close()
                self._lease = None
