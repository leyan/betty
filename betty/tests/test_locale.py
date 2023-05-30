from __future__ import annotations

import difflib
from pathlib import Path
from typing import List, Iterator, Set, Tuple, cast

import pytest

from betty.fs import FileSystem, ASSETS_DIRECTORY_PATH
from betty.locale import Localized, negotiate_localizeds, Date, DateRange, negotiate_locale, \
    Datey, LocalizerRepository, Localey, DEFAULT_LOCALIZER, to_locale, update_translations
from betty.tempfile import TemporaryDirectory


class TestPotFile:
    def _readlines(self, assets_directory_path: Path) -> Iterator[str]:
        with open(assets_directory_path / 'betty.pot') as f:
            return filter(
                lambda line: not line.startswith((
                    '# Copyright (C) ',
                    '# FIRST AUTHOR <EMAIL@ADDRESS>, ',
                    '"POT-Creation-Date: ',
                    '"PO-Revision-Date: ',
                    '"Generated-By: ',
                )),
                f.readlines(),
            )

    def test(self) -> None:
        with TemporaryDirectory() as working_directory_path:
            update_translations(working_directory_path)
            actual_pot_contents = self._readlines(ASSETS_DIRECTORY_PATH)
            expected_pot_contents = self._readlines(working_directory_path)
            diff = difflib.unified_diff(
                list(actual_pot_contents),
                list(expected_pot_contents),
            )
            assert 0 == len(list(diff)), 'The gettext *.po files are not up to date. Did you run `betty update-translations`?'


class TestDate:
    def test_year(self):
        year = 1970
        sut = Date(year=year)
        assert year == sut.year

    def test_month(self):
        month = 1
        sut = Date(month=month)
        assert month == sut.month

    def test_day(self):
        day = 1
        sut = Date(day=day)
        assert day == sut.day

    def test_fuzzy(self):
        fuzzy = True
        sut = Date()
        sut.fuzzy = fuzzy
        assert fuzzy == sut.fuzzy

    @pytest.mark.parametrize('expected, year, month, day', [
        (True, 1970, 1, 1),
        (False, None, 1, 1),
        (True, 1970, None, 1),
        (True, 1970, 1, None),
        (False, None, None, 1),
        (True, 1970, None, None),
        (False, None, None, None),
    ])
    def test_comparable(self, expected, year, month, day):
        sut = Date(year, month, day)
        assert expected == sut.comparable

    @pytest.mark.parametrize('expected, year, month, day', [
        (True, 1970, 1, 1),
        (False, None, 1, 1),
        (False, 1970, None, 1),
        (False, 1970, 1, None),
        (False, None, None, 1),
        (False, 1970, None, None),
        (False, None, None, None),
    ])
    def test_complete(self, expected, year, month, day):
        sut = Date(year, month, day)
        assert expected == sut.complete

    def test_to_range_when_incomparable_should_raise(self):
        with pytest.raises(ValueError):
            Date(None, 1, 1).to_range()

    @pytest.mark.parametrize('year, month, day', [
        (1970, 1, 1),
        (None, None, None),
    ])
    def test_parts(self, year, month, day):
        assert (year, month, day) == Date(year, month, day).parts

    @pytest.mark.parametrize('expected, other', [
        (False, Date(1970, 2, 1)),
        (True, Date(1970, 2, 2)),
        (False, Date(1970, 2, 3)),
        (False, DateRange()),
    ])
    def test_in(self, expected, other):
        assert expected == (other in Date(1970, 2, 2))

    @pytest.mark.parametrize('expected, other', [
        (False, Date(1970, 2, 1)),
        (False, Date(1970, 2, 2)),
        (True, Date(1970, 2, 3)),
        (False, Date(1970)),
        (False, Date(1970, 2)),
        (True, Date(1971)),
        (True, Date(1970, 3)),
    ])
    def test_lt(self, expected, other):
        assert expected == (Date(1970, 2, 2) < other)

    @pytest.mark.parametrize('expected, other', [
        (True, Date(1970, 1, 1)),
        (False, Date(1970, 1, None)),
        (False, Date(1970, None, 1)),
        (False, Date(None, 1, 1)),
        (False, Date(1970, None, None)),
        (False, Date(None, 1, None)),
        (False, Date(None, None, 1)),
        (False, None),
    ])
    def test_eq(self, expected, other):
        assert expected == (Date(1970, 1, 1) == other)
        assert expected == (other == Date(1970, 1, 1))

    @pytest.mark.parametrize('expected, other', [
        (True, Date(1970, 2, 1)),
        (False, Date(1970, 2, 2)),
        (False, Date(1970, 2, 3)),
    ])
    def test_gt(self, expected, other):
        assert expected == (Date(1970, 2, 2) > other)


class TestDateRange:
    _TEST_IN_PARAMETERS: List[Tuple[bool, Datey, Datey]] = [
        (False, Date(1970, 2, 2), DateRange()),
        (False, Date(1970, 2), DateRange()),
        (False, Date(1970), DateRange()),
        (False, Date(1970, 2, 1), DateRange(Date(1970, 2, 2))),
        (True, Date(1970, 2, 2), DateRange(Date(1970, 2, 2))),
        (True, Date(1970, 2, 3), DateRange(Date(1970, 2, 2))),
        (True, Date(1970, 2, 1), DateRange(None, Date(1970, 2, 2))),
        (True, Date(1970, 2, 2), DateRange(None, Date(1970, 2, 2))),
        (False, Date(1970, 2, 3), DateRange(None, Date(1970, 2, 2))),
        (False, Date(1969, 2, 1), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (True, Date(1970, 2, 1), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (False, Date(1971, 2, 1), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 1)), DateRange(Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 2)), DateRange(Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 3)), DateRange(Date(1970, 2, 2))),
        (False, DateRange(None, Date(1970, 2, 1)), DateRange(Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 2)), DateRange(Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 3)), DateRange(Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 1)), DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 2)), DateRange(None, Date(1970, 2, 2))),
        (False, DateRange(Date(1970, 2, 3)), DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 1)), DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 2)), DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 3)), DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(Date(1969, 2, 1)), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 1)), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (False, DateRange(Date(1971, 2, 1)), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (False, DateRange(None, Date(1969, 2, 1)), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 1)), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (True, DateRange(None, Date(1971, 2, 1)), DateRange(Date(1969, 2, 2), Date(1970, 2, 2))),
        (False, DateRange(Date(1969, 2, 2), Date(1970, 2, 2)), DateRange(Date(1971, 2, 2), Date(1972, 2, 2))),
        (True, DateRange(Date(1969, 2, 2), Date(1971, 2, 2)), DateRange(Date(1970, 2, 2), Date(1972, 2, 2))),
        (True, DateRange(Date(1970, 2, 2), Date(1971, 2, 2)), DateRange(Date(1969, 2, 2), Date(1972, 2, 2))),
    ]

    # Mirror the arguments because we want the containment check to work in either direction.
    @pytest.mark.parametrize('expected, other, sut', _TEST_IN_PARAMETERS + list(map(lambda x: (x[0], x[2], x[1]), _TEST_IN_PARAMETERS)))
    def test_in(self, expected: bool, other: Datey, sut: Datey):
        assert expected == (other in sut)

    @pytest.mark.parametrize('expected, other', [
        (False, Date(1970, 2, 1)),
        (False, Date(1970, 2, 2)),
        (True, Date(1970, 2, 3)),
        (False, DateRange(Date(1970, 2, 1))),
        (False, DateRange(Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 3))),
        (False, DateRange(None, Date(1970, 2, 1))),
        (False, DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 3))),
        (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 2))),
        (False, DateRange(Date(1970, 2, 2), Date(1970, 2, 3))),
        (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 3))),
    ])
    def test_lt_with_start_date(self, expected, other):
        assert expected == (DateRange(Date(1970, 2, 2)) < other)

    @pytest.mark.parametrize('expected, other', [
        (False, Date(1970, 2, 1)),
        (True, Date(1970, 2, 2)),
        (True, Date(1970, 2, 3)),
        (False, DateRange(Date(1970, 2, 1))),
        (True, DateRange(Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 3))),
        (False, DateRange(None, Date(1970, 2, 1))),
        (False, DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 3))),
        (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 2), Date(1970, 2, 3))),
        (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 3))),
    ])
    def test_lt_with_end_date(self, expected, other):
        assert expected == (DateRange(None, Date(1970, 2, 2)) < other)

    @pytest.mark.parametrize('expected, other', [
        (False, Date(1970, 2, 1)),
        (True, Date(1970, 2, 2)),
        (True, Date(1970, 2, 3)),
        (False, DateRange(Date(1970, 1, 1))),
        (True, DateRange(Date(1970, 2, 1))),
        (True, DateRange(Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 3))),
        (False, DateRange(None, Date(1970, 2, 1))),
        (True, DateRange(None, Date(1970, 2, 2))),
        (True, DateRange(None, Date(1970, 2, 3))),
        (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 2), Date(1970, 2, 3))),
        (False, DateRange(Date(1970, 2, 1), Date(1970, 2, 3))),
    ])
    def test_lt_with_both_dates(self, expected, other):
        assert expected == (DateRange(Date(1970, 2, 1), Date(1970, 2, 3)) < other)

    @pytest.mark.parametrize('expected, other', [
        (True, DateRange(Date(1970, 2, 2))),
        (False, DateRange(Date(1970, 2, None))),
        (False, DateRange(Date(1970, None, 2))),
        (False, DateRange(Date(None, 2, 2))),
        (False, DateRange(Date(1970, None, None))),
        (False, DateRange(Date(None, 2, None))),
        (False, DateRange(Date(None, None, 2))),
        (False, None),
    ])
    def test_eq(self, expected, other):
        assert expected == (DateRange(Date(1970, 2, 2)) == other)

    @pytest.mark.parametrize('expected, other', [
        (True, Date(1970, 2, 1)),
        (True, Date(1970, 2, 2)),
        (False, Date(1970, 2, 3)),
        (True, DateRange(Date(1970, 2, 1))),
        (False, DateRange(Date(1970, 2, 2))),
        (False, DateRange(Date(1970, 2, 3))),
        (True, DateRange(None, Date(1970, 2, 1))),
        (True, DateRange(None, Date(1970, 2, 2))),
        (False, DateRange(None, Date(1970, 2, 3))),
        (True, DateRange(Date(1970, 2, 1), Date(1970, 2, 2))),
        (True, DateRange(Date(1970, 2, 2), Date(1970, 2, 3))),
        (True, DateRange(Date(1970, 2, 1), Date(1970, 2, 3))),
    ])
    def test_gt(self, expected, other):
        assert expected == (DateRange(Date(1970, 2, 2)) > other)


class TestNegotiateLocale:
    @pytest.mark.parametrize('expected, preferred_locale, available_locales', [
        ('nl', 'nl', {'nl'}),
        ('nl-NL', 'nl', {'nl-NL'}),
        ('nl', 'nl-NL', {'nl'}),
        ('nl-NL', 'nl-NL', {'nl', 'nl-BE', 'nl-NL'}),
        ('nl', 'nl', {'nl', 'en'}),
        ('nl', 'nl', {'en', 'nl'}),
        ('nl-NL', 'nl-BE', {'nl-NL'}),
    ])
    def test(self, expected: Localey | None, preferred_locale: Localey, available_locales: Set[Localey]):
        actual = negotiate_locale(preferred_locale, available_locales)
        assert expected == (to_locale(actual) if actual else actual)


class TestNegotiateLocalizeds:
    class DummyLocalized(Localized):
        def __eq__(self, other):
            return self.locale == other.locale

        def __repr__(self):
            return '%s(%s)' % (self.__class__.__name__, self.locale)

    @pytest.mark.parametrize('expected, preferred_locale, localizeds', [
        (DummyLocalized('nl'), 'nl', [DummyLocalized('nl')]),
        (DummyLocalized('nl-NL'), 'nl', [DummyLocalized('nl-NL')]),
        (DummyLocalized('nl'), 'nl-NL', [DummyLocalized('nl')]),
        (DummyLocalized('nl-NL'), 'nl-NL', [DummyLocalized('nl'), DummyLocalized('nl-BE'), DummyLocalized('nl-NL')]),
        (DummyLocalized('nl'), 'nl', [DummyLocalized('nl'), DummyLocalized('en')]),
        (DummyLocalized('nl'), 'nl', [DummyLocalized('en'), DummyLocalized('nl')]),
        (DummyLocalized('nl-NL'), 'nl-BE', [DummyLocalized('nl-NL')]),
        (None, 'nl', []),
    ])
    def test_with_match_should_return_match(self, expected: Localized | None, preferred_locale: str, localizeds: List[Localized]):
        assert expected == negotiate_localizeds(preferred_locale, localizeds)

    def test_without_match_should_return_default(self):
        preferred_locale = 'de'
        localizeds = [self.DummyLocalized('nl'), self.DummyLocalized('en'), self.DummyLocalized('uk')]
        assert self.DummyLocalized('nl') == negotiate_localizeds(preferred_locale, localizeds)


class TestDefaultLocalizer:
    _FORMAT_DATE_TEST_PARAMETERS: List[Tuple[str, Date]] = [
        # Dates that cannot be formatted.
        ('unknown date', Date()),
        ('unknown date', Date(None, None, 1)),
        # Single dates.
        ('January', Date(None, 1, None)),
        ('around January', Date(None, 1, None, fuzzy=True)),
        ('1970', Date(1970, None, None)),
        ('around 1970', Date(1970, None, None, fuzzy=True)),
        ('January, 1970', Date(1970, 1, None)),
        ('around January, 1970', Date(1970, 1, None, fuzzy=True)),
        ('January 1, 1970', Date(1970, 1, 1)),
        ('around January 1, 1970', Date(1970, 1, 1, fuzzy=True)),
        ('January 1', Date(None, 1, 1)),
        ('around January 1', Date(None, 1, 1, fuzzy=True)),
    ]

    @pytest.mark.parametrize('expected, date', _FORMAT_DATE_TEST_PARAMETERS)
    def test_format_date(self, expected: str, date: Date):
        sut = DEFAULT_LOCALIZER
        assert expected == sut.format_date(date)

    _FORMAT_DATE_RANGE_TEST_PARAMETERS: List[Tuple[str, DateRange]] = [
        ('from January 1, 1970 until December 31, 1999', DateRange(Date(1970, 1, 1), Date(1999, 12, 31))),
        ('from January 1, 1970 until sometime before December 31, 1999', DateRange(Date(1970, 1, 1), Date(1999, 12, 31), end_is_boundary=True)),
        ('from January 1, 1970 until around December 31, 1999', DateRange(Date(1970, 1, 1), Date(1999, 12, 31, fuzzy=True))),
        ('from January 1, 1970 until sometime before around December 31, 1999', DateRange(Date(1970, 1, 1), Date(1999, 12, 31, fuzzy=True), end_is_boundary=True)),
        ('from sometime after January 1, 1970 until December 31, 1999', DateRange(Date(1970, 1, 1), Date(1999, 12, 31), start_is_boundary=True)),
        ('sometime between January 1, 1970 and December 31, 1999', DateRange(Date(1970, 1, 1), Date(1999, 12, 31), start_is_boundary=True, end_is_boundary=True)),
        ('from sometime after January 1, 1970 until around December 31, 1999', DateRange(Date(1970, 1, 1), Date(1999, 12, 31, fuzzy=True), start_is_boundary=True)),
        ('sometime between January 1, 1970 and around December 31, 1999', DateRange(Date(1970, 1, 1), Date(1999, 12, 31, fuzzy=True), start_is_boundary=True, end_is_boundary=True)),
        ('from around January 1, 1970 until December 31, 1999', DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31))),
        ('from around January 1, 1970 until sometime before December 31, 1999', DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31), end_is_boundary=True)),
        ('from around January 1, 1970 until around December 31, 1999', DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31, fuzzy=True))),
        ('from around January 1, 1970 until sometime before around December 31, 1999', DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31, fuzzy=True), end_is_boundary=True)),
        ('from sometime after around January 1, 1970 until December 31, 1999', DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31), start_is_boundary=True)),
        ('sometime between around January 1, 1970 and December 31, 1999', DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31), start_is_boundary=True, end_is_boundary=True)),
        ('from sometime after around January 1, 1970 until around December 31, 1999', DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31, fuzzy=True), start_is_boundary=True)),
        ('sometime between around January 1, 1970 and around December 31, 1999', DateRange(Date(1970, 1, 1, fuzzy=True), Date(1999, 12, 31, fuzzy=True), start_is_boundary=True, end_is_boundary=True)),
        ('from January 1, 1970', DateRange(Date(1970, 1, 1))),
        ('sometime after January 1, 1970', DateRange(Date(1970, 1, 1), start_is_boundary=True)),
        ('from around January 1, 1970', DateRange(Date(1970, 1, 1, fuzzy=True))),
        ('sometime after around January 1, 1970', DateRange(Date(1970, 1, 1, fuzzy=True), start_is_boundary=True)),
        ('until December 31, 1999', DateRange(None, Date(1999, 12, 31))),
        ('sometime before December 31, 1999', DateRange(None, Date(1999, 12, 31), end_is_boundary=True)),
        ('until around December 31, 1999', DateRange(None, Date(1999, 12, 31, fuzzy=True))),
        ('sometime before around December 31, 1999', DateRange(None, Date(1999, 12, 31, fuzzy=True), end_is_boundary=True)),
    ]

    @pytest.mark.parametrize('expected, date_range', _FORMAT_DATE_RANGE_TEST_PARAMETERS)
    def test_format_date_range(self, expected: str, date_range: DateRange):
        sut = DEFAULT_LOCALIZER
        assert expected == sut.format_date_range(date_range)

    _FORMAT_DATEY_TEST_PARAMETERS = cast(List[Tuple[str, Datey]], _FORMAT_DATE_TEST_PARAMETERS) + cast(List[Tuple[str, Datey]], _FORMAT_DATE_RANGE_TEST_PARAMETERS)

    @pytest.mark.parametrize('expected, datey', _FORMAT_DATEY_TEST_PARAMETERS)
    def test_format_datey(self, expected: str, datey: Datey):
        sut = DEFAULT_LOCALIZER
        assert expected == sut.format_datey(datey)


class TestLocalizerRepository:
    def test_getitem(self) -> None:
        locale = 'nl-NL'
        with TemporaryDirectory() as assets_directory_path_str:
            fs = FileSystem((assets_directory_path_str, None))
            assets_directory_path = Path(assets_directory_path_str)
            lc_messages_directory_path = assets_directory_path / 'locale' / locale
            lc_messages_directory_path.mkdir(parents=True)
            po = """
# Dutch translations for PROJECT.
# Copyright (C) 2019 ORGANIZATION
# This file is distributed under the same license as the PROJECT project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2019.
#
msgid ""
msgstr ""
"Project-Id-Version: PROJECT VERSION\n"
"Report-Msgid-Bugs-To: EMAIL@ADDRESS\n"
"POT-Creation-Date: 2020-11-18 23:28+0000\n"
"PO-Revision-Date: 2019-10-05 11:38+0100\n"
"Last-Translator: \n"
"Language: nl\n"
"Language-Team: nl <LL@li.org>\n"
"Plural-Forms: nplurals=2; plural=(n != 1)\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel 2.7.0\n"95

#: betty/ancestry.py:457
msgid "Subject"
msgstr "Onderwerp"
"""
            with open(lc_messages_directory_path / 'betty.po', 'w') as f:
                f.write(po)
            sut = LocalizerRepository(fs)
            assert 'Onderwerp' == sut[locale]._('Subject')
