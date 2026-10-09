"""Private, credential-free DOCX worker. Not an application/server entry point."""
import json
from pathlib import Path
import resource
import sys


def set_limits():
    # Limits precede importing XML/archive parsers or reading untrusted bytes.
    resource.setrlimit(resource.RLIMIT_AS, (128 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def main():
    set_limits()
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from project_files import MAX_TOTAL_BYTES, ProjectInputError
    from research_files import MAX_RESEARCH_BYTES, MAX_DOCX_RESULT_BYTES, _docx_in_process
    try:
        data = sys.stdin.buffer.read(MAX_RESEARCH_BYTES + 1)
        if len(data) > MAX_RESEARCH_BYTES:
            raise ProjectInputError('document.docx exceeds the 10 MB research-document limit.')
        file = _docx_in_process('document.docx', data)
        if len(file.content.encode('utf-8')) > MAX_TOTAL_BYTES:
            raise ProjectInputError('Research text exceeds the 600 KB analysis limit.')
        result = {'content': file.content, 'locations': file.locations, 'detail': file.detail}
    except ProjectInputError as error:
        result = {'error': str(error)}
    output = json.dumps(result, ensure_ascii=False).encode('utf-8')
    if len(output) > MAX_DOCX_RESULT_BYTES:
        output = b'{"error":"document.docx has too many extracted locations to process safely."}'
    sys.stdout.buffer.write(output)


if __name__ == '__main__':
    main()
