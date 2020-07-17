from requests import exceptions


class ResponseMock:
    """Simple mock of a HTTP response."""

    def __init__(self, code, data=None, raw=None):
        self.status_code = code
        self.data = data
        self.raw = raw

    def raise_for_status(self):
        if self.status_code != 200:
            raise exceptions.HTTPError

    def json(self):
        self.raise_for_status()
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def compare_lines(expected_path, path, num_lines):
    """Compares the first n lines of two files.

    Args:
        expected_path: Path to the file with the expected content, as a string.
        path: Path to the file to compare with the expected file, as a string.
        num_lines: Number of lines to compare, as an int.

    Returns:
        True, if the two files have the same content. False, otherwise.
    """
    with open(expected_path, 'rb') as expected, open(path, 'rb') as file:
        for i in range(num_lines):
            line1 = expected.readline()
            line2 = file.readline()
            if line1 != line2:
                print('WANT:', line1)
                print('GOT:', line2)
                return False
    return True
