SERVICES['node']['monitoring']['Raven'] = {
    'request': {
        'url': 'http://10.0.2.15:8096/wps?service=WPS&version=1.0.0&request=GetCapabilities'
    }
}
SERVICES['raven'] = {
    'info': {
        'name': 'Hydrological modeling and analysis',
        'synopsis': ('A suite of WPS processes to calibrate and run hydrological models, including geographical'
        'information retrieval and processing as well as time series analysis.'),
        'version': '0.11.1',
        'institution': 'Ouranos',
        'releaseTime': '2021-02-01T00:00:00Z',
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
                'url': 'https://10.0.2.15/twitcher/ows/proxy/raven?service=WPS&version=1.0.0&request=GetCapabilities'
            }
        },
    }
}
