SERVICES['Catalog'] = {
    'info': {
        'name': 'Catalog',
        'synopsis': 'Catalog',
        'version': "0.6.11",
        'institution': 'Ouranos',
        'releaseTime': get_release_time_from_repo_tag("docker", "pavics/pavics-datacatalog", "0.6.11"),
        'researchSubject': 'Climate',
        'supportEmail': 'helpdesk@example.com',
        'category': 'Catalog',
        'tags': ['Catalog', 'Data']
    },
    'stats': {
        'method': '.*',
        'route': 'http://10.0.2.15:8086/.*'
    },
    'redirect': {
        'doc': 'https://ouranosinc.github.io/pavics-sdi/arch/data_catalog.html#pavics-datacatalog',
        'releasenotes': 'https://github.com/Ouranosinc/PAVICS-DataCatalog/blob/master/CHANGES.md',
        'support': 'https://github.com/ouranosinc/PAVICS-DataCatalog/issues',
        'source': 'https://github.com/ouranosinc/PAVICS-DataCatalog',
        'tryme': 'http://10.0.2.15:8086/pywps?service=WPS&version=1.0.0&request=GetCapabilities',
        'licence': 'https://ouranosinc.github.io/pavics-sdi/arch/data_catalog.html#credits',
        'provenance': 'https://ouranosinc.github.io/pavics-sdi/arch/data_catalog.html#pavics-datacatalog'
    },
    "monitoring": {
        "Catalog": {
            'request': {
                # FIXME: remove port by design (https://github.com/bird-house/birdhouse-deploy/issues/222)
                'url': 'http://10.0.2.15:8086/pywps?service=WPS&version=1.0.0&request=GetCapabilities'
            }
        }
    }
}
