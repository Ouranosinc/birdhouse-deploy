RAVEN_VERSION = "0.18.1"
RAVEN_RELEASE = get_release_time_from_repo_tag("github", "Ouranosinc/raven", RAVEN_VERSION)

SERVICES['raven'] = {
    'info': {
        'name': 'Hydrological modeling and analysis',
        'synopsis': (
            'A suite of WPS processes to calibrate and run hydrological models, '
            'including geographical information retrieval and processing as well as time series analysis.'
        ),
        'version': RAVEN_VERSION,
        'institution': 'Ouranos',
        'releaseTime': RAVEN_RELEASE,
        'researchSubject': 'Hydrology',
        'supportEmail': 'helpdesk@example.com',
        'category': 'Data Manipulation',
        'tags': ['Hydrology']
    },
    'stats': {
        'method': '.*',
        'route': '/twitcher/ows/proxy/raven.*'
    },
    'redirect': {
        'doc': 'https://pavics-raven.readthedocs.io/en/latest/',
        'releasenotes': 'https://github.com/Ouranosinc/raven/releases',
        'support': 'https://github.com/Ouranosinc/raven/issues',
        'source': 'https://github.com/Ouranosinc/raven',
        'tryme': 'https://pavics-raven.readthedocs.io/en/latest/notebooks/index.html',
        'licence': 'https://github.com/Ouranosinc/raven/blob/master/LICENSE.txt',
        'provenance': 'https://ouranosinc.github.io/pavics-sdi/provenance/index.html'
    },
    'monitoring': {
        'Raven': {
            'request': {
                'url': 'http://raven:9099/wps?service=WPS&version=1.0.0&request=GetCapabilities'
            }
        },
    }
}
