from betty.cotton_candy import CottonCandy
from betty.model.ancestry import PersonName, Citation, Source, Person
from betty.tests import TemplateTestCase


class TestNameLabel(TemplateTestCase):
    extensions = {CottonCandy}
    template_string = '{% import \'macro/person.html.j2\' as personMacros %}{{ personMacros.name_label(name, embedded=embedded if embedded is defined else False) }}'

    def test_with_full_name(self):
        person = Person(None)
        name = PersonName(person, 'Jane', 'Dough')
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span>'
        with self._render(data={
            'name': name,
        }) as (actual, _):
            assert expected == actual

    def test_with_individual_name(self):
        person = Person(None)
        name = PersonName(person, 'Jane')
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span></span>'
        with self._render(data={
            'name': name,
        }) as (actual, _):
            assert expected == actual

    def test_with_affiliation_name(self):
        person = Person(None)
        name = PersonName(person, None, 'Dough')
        expected = '<span class="person-label" typeof="foaf:Person">… <span property="foaf:familyName">Dough</span></span>'
        with self._render(data={
            'name': name,
        }) as (actual, _):
            assert expected == actual

    def test_embedded(self):
        person = Person(None)
        name = PersonName(person, 'Jane', 'Dough')
        source = Source(None)
        citation = Citation(None, source)
        name.citations.append(citation)
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span>'
        with self._render(data={
            'name': name,
            'embedded': True,
        }) as (actual, _):
            assert expected == actual

    def test_with_citation(self):
        person = Person(None)
        name = PersonName(person, 'Jane')
        source = Source(None)
        citation = Citation(None, source)
        name.citations.append(citation)
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span></span><a href="#reference-1" class="citation">[1]</a>'
        with self._render(data={
            'name': name,
        }) as (actual, _):
            assert expected == actual
