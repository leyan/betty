from typing import Dict, TYPE_CHECKING

from betty import about
from betty.app import App
from betty.media_type import EXTENSIONS

if TYPE_CHECKING:
    from betty.builtins import _


class _Resource:
    def __init__(self, name: str, collection_endpoint_summary: str, collection_response_description: str,
                 single_endpoint_summary: str, single_response_description):
        self.name = name
        self.collection_endpoint_summary = collection_endpoint_summary
        self.collection_response_description = collection_response_description
        self.single_endpoint_summary = single_endpoint_summary
        self.single_response_description = single_response_description


def _get_resources():
    return [
        _Resource(
            'file',
            _('Retrieve the collection of files.'),
            _('The collection of files.'),
            _('Retrieve a single file.'),
            _('The file.'),
        ),
        _Resource(
            'person',
            _('Retrieve the collection of people.'),
            _('The collection of people.'),
            _('Retrieve a single person.'),
            _('The person.'),
        ),
        _Resource(
            'place',
            _('Retrieve the collection of places.'),
            _('The collection of places.'),
            _('Retrieve a single place.'),
            _('The place.'),
        ),
        _Resource(
            'event',
            _('Retrieve the collection of events.'),
            _('The collection of events.'),
            _('Retrieve a single event.'),
            _('The event.'),
        ),
        _Resource(
            'citation',
            _('Retrieve the collection of citations.'),
            _('The collection of citations.'),
            _('Retrieve a single citation.'),
            _('The citation.'),
        ),
        _Resource(
            'source',
            _('Retrieve the collection of sources.'),
            _('The collection of sources.'),
            _('Retrieve a single source.'),
            _('The source.'),
        ),
    ]


def build_specification(app: App) -> Dict:
    specification = {
        'openapi': '3.0.0',
        'servers': [
            {
                'url': app.static_url_generator.generate('/', absolute=True),
            }
        ],
        'info': {
            'title': 'Betty',
            'version': about.version()
        },
        'paths': {},
        'components': {
            'responses': {
                '401': {
                    'description': _('Unauthorized'),
                    'content': {
                        'application/json': {
                            'schema': {
                                '$ref': '#/components/schemas/betty/error',
                            },
                        },
                    },
                },
                '403': {
                    'description': _('Forbidden'),
                    'content': {
                        'application/json': {
                            'schema': {
                                '$ref': '#/components/schemas/betty/error',
                            },
                        },
                    },
                },
                '404': {
                    'description': _('Not found'),
                    'content': {
                        'application/json': {
                            'schema': {
                                '$ref': '#/components/schemas/betty/error',
                            },
                        },
                    },
                },
            },
            'parameters': {
                'id': {
                    'name': 'id',
                    'in': 'path',
                    'required': True,
                    'description': _('The ID for the resource to retrieve.'),
                    'schema': {
                        'type': 'string',
                    },
                },
            },
            'headers': {
                'Content-Language': {
                    'description': _('An HTTP [Content-Language](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Language) header.'),
                    'schema': {
                        'type': 'string',
                    },
                    'example': app.project.configuration.locales.default.locale,
                },
            },
            'schemas': {
                'betty': {
                    '$ref': app.static_url_generator.generate('/schema.json#/definitions'),
                },
            },
        },
    }

    # Add resource operations.
    for resource in _get_resources():
        if app.project.configuration.content_negotiation:
            collection_path = '/%s/' % resource.name
            single_path = '/%s/{id}/' % resource.name
        else:
            collection_path = '/{locale}/%s/index.json' % resource.name
            single_path = '/{locale}/%s/{id}/index.json' % resource.name
        specification['paths'].update({  # type: ignore
            collection_path: {
                'get': {
                    'summary': resource.collection_endpoint_summary,
                    'responses': {
                        '200': {
                            'description': resource.collection_response_description,
                            'content': {
                                'application/json': {
                                    'schema': {
                                        '$ref': '#/components/schemas/betty/%sCollection' % resource.name,
                                    },
                                },
                            },
                        },
                    },
                },
            },
            single_path: {
                'get': {
                    'summary': resource.single_endpoint_summary,
                    'responses': {
                        '200': {
                            'description': resource.single_response_description,
                            'content': {
                                'application/json': {
                                    'schema': {
                                        '$ref': '#/components/schemas/betty/%s' % resource.name,
                                    },
                                },
                            },
                        },
                    },
                },
            },
        })

    # Add components for content negotiation.
    if app.project.configuration.content_negotiation:
        specification['components']['parameters']['Accept'] = {  # type: ignore
            'name': 'Accept',
            'in': 'header',
            'description': _('An HTTP [Accept](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept) header.'),
            'schema': {
                'enum': list(EXTENSIONS.keys()),
            },
        }
        specification['components']['parameters']['Accept-Language'] = {  # type: ignore
            'name': 'Accept-Language',
            'in': 'header',
            'description': _('An HTTP [Accept-Language](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept-Language) header.'),
            'schema': {
                'type': 'string',
            },
            'example': app.project.configuration.locales[app.project.configuration.locales.default.locale].alias,
        }
        specification['components']['schemas']['html'] = {  # type: ignore
            'type': 'string',
            'description': _('An HTML5 document.'),
        }
    else:
        specification['components']['parameters']['locale'] = {  # type: ignore
            'name': 'locale',
            'in': 'path',
            'required': True,
            'description': _('A locale name.'),
            'schema': {
                'type': 'string',
                'enum': [locale_configuration.locale for locale_configuration in app.project.configuration.locales],
            },
            'example': app.project.configuration.locales[app.project.configuration.locales.default.locale].alias,
        }

    # Add default behavior to all requests.
    for path in specification['paths']:
        specification['paths'][path]['get']['responses'].update({  # type: ignore
            '401': {
                '$ref': '#/components/responses/401',
            },
            '403': {
                '$ref': '#/components/responses/403',
            },
            '404': {
                '$ref': '#/components/responses/404',
            },
        })
        if app.project.configuration.content_negotiation:
            specification['paths'][path]['parameters'] = [  # type: ignore
                {
                    '$ref': '#/components/parameters/Accept',
                },
                {
                    '$ref': '#/components/parameters/Accept-Language',
                },
            ]
        else:
            specification['paths'][path]['parameters'] = [  # type: ignore
                {
                    '$ref': '#/components/parameters/locale',
                },
            ]

    # Add default behavior to all responses.
    if app.project.configuration.content_negotiation:
        responses = list(specification['components']['responses'].values())  # type: ignore
        for path in specification['paths']:
            responses.append(
                specification['paths'][path]['get']['responses']['200'])  # type: ignore
        for response in responses:
            response['content']['text/html'] = {
                'schema': {
                    '$ref': '#/components/schemas/html'
                }
            }
            if 'headers' not in response:
                response['headers'] = {}
            response['headers']['Content-Language'] = {
                '$ref': '#/components/headers/Content-Language',
            }

    return specification
