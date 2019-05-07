import os
from os import mkdir
from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.fs import iterfiles, FileSystem


class IterfilesTest(TestCase):
    def test_iterfiles(self):
        with TemporaryDirectory() as path:
            subdirpath = join(path, 'subdir')
            mkdir(subdirpath)
            open(join(path, 'rootfile'), 'a').close()
            open(join(path, '.hiddenrootfile'), 'a').close()
            open(join(subdirpath, 'subdirfile'), 'a').close()
            actual = [actualpath[len(path) + 1:]
                      for actualpath in iterfiles(path)]
        expected = [
            '.hiddenrootfile',
            'rootfile',
            'subdir/subdirfile',
        ]
        self.assertCountEqual(expected, actual)


class FileSystemTest(TestCase):
    def test_open(self):
        with TemporaryDirectory() as source_path_1:
            with TemporaryDirectory() as source_path_2:
                with open(join(source_path_1, 'apples'), 'w') as f:
                    f.write('apples')
                with open(join(source_path_2, 'apples'), 'w') as f:
                    f.write('notapples')
                with open(join(source_path_1, 'oranges'), 'w') as f:
                    f.write('oranges')
                with open(join(source_path_2, 'bananas'), 'w') as f:
                    f.write('bananas')

                sut = FileSystem(source_path_1, source_path_2)

                with sut.open('apples') as f:
                    self.assertEquals('apples', f.read())
                with sut.open('oranges') as f:
                    self.assertEquals('oranges', f.read())
                with sut.open('bananas') as f:
                    self.assertEquals('bananas', f.read())

                with self.assertRaises(FileNotFoundError):
                    sut.open('mangos')

    def test_copy2(self):
        with TemporaryDirectory() as source_path_1:
            with TemporaryDirectory() as source_path_2:
                with open(join(source_path_1, 'apples'), 'w') as f:
                    f.write('apples')
                with open(join(source_path_2, 'apples'), 'w') as f:
                    f.write('notapples')
                with open(join(source_path_1, 'oranges'), 'w') as f:
                    f.write('oranges')
                with open(join(source_path_2, 'bananas'), 'w') as f:
                    f.write('bananas')

                with TemporaryDirectory() as destination_path:
                    sut = FileSystem(source_path_1, source_path_2)

                    sut.copy2('apples', destination_path)
                    sut.copy2('oranges', destination_path)
                    sut.copy2('bananas', destination_path)

                    with sut.open(join(destination_path, 'apples')) as f:
                        self.assertEquals('apples', f.read())
                    with sut.open(join(destination_path, 'oranges')) as f:
                        self.assertEquals('oranges', f.read())
                    with sut.open(join(destination_path, 'bananas')) as f:
                        self.assertEquals('bananas', f.read())

                    with self.assertRaises(FileNotFoundError):
                        sut.copy2('mangos', destination_path)

    def test_copytree(self):
        with TemporaryDirectory() as source_path_1:
            os.makedirs(join(source_path_1, 'basket'))
            with TemporaryDirectory() as source_path_2:
                os.makedirs(join(source_path_2, 'basket'))
                with open(join(source_path_1, 'basket', 'apples'), 'w') as f:
                    f.write('apples')
                with open(join(source_path_2, 'basket', 'apples'), 'w') as f:
                    f.write('notapples')
                with open(join(source_path_1, 'basket', 'oranges'), 'w') as f:
                    f.write('oranges')
                with open(join(source_path_2, 'basket', 'bananas'), 'w') as f:
                    f.write('bananas')

                with TemporaryDirectory() as destination_path:
                    sut = FileSystem(source_path_1, source_path_2)

                    sut.copytree('', destination_path)

                    with sut.open(join(destination_path, 'basket', 'apples')) as f:
                        self.assertEquals('apples', f.read())
                    with sut.open(join(destination_path, 'basket', 'oranges')) as f:
                        self.assertEquals('oranges', f.read())
                    with sut.open(join(destination_path, 'basket', 'bananas')) as f:
                        self.assertEquals('bananas', f.read())
