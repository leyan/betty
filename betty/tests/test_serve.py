from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep

import requests

from betty.asyncio import sync
from betty.serve import BuiltinServer
from betty.tests import TestCase


class BuiltinServerTest(TestCase):
    @sync
    async def test(self):
        content = 'Hello, and welcome to my site!'
        with TemporaryDirectory() as www_directory_path:
            with open(Path(www_directory_path) / 'index.html', 'w') as f:
                f.write(content)
            async with BuiltinServer(www_directory_path) as server:
                # Wait for the server to start.
                sleep(1)
                response = requests.get(server.public_url)
                self.assertEquals(200, response.status_code)
                self.assertEquals(content, response.content.decode('utf-8'))
                self.assertEquals('no-cache', response.headers['Cache-Control'])
