SERVICES['renderer'] = {
    'info': {
        'name': 'High-resolution spatial gridded data renderer',
        'synopsis': (
            'This service renders gridded data on the server and sends images to the client for display within '
            'mapping applications using Open Geospatial Consortium (OGC) Web Mappping Service (WMS) standard.'
        ),
        'version': '4.6.15',
        'institution': 'Unidata',
        'releaseTime': '2020-06-16T00:00:00Z',
        'researchSubject': 'Climatology',
        'supportEmail': 'helpdesk@example.com',
        'category': 'Data Manipulation',
        'tags': ['Climatology']
    },
    'stats': {
        'method': '.*',
        'route': '/thredds/.*'
    },
    'redirect': {
        'doc': 'https://ouranosinc.github.io/pavics-sdi/arch/frontend.html#gridded-data-rendering',
        'releasenotes': 'https://github.com/Unidata/tds/releases',
        'support': 'https://github.com/Ouranosinc/pavics-sdi/issues',
        'source': 'https://github.com/Unidata/tds',
        'tryme': 'https://ouranosinc.github.io/pavics-sdi/notebooks/rendering.html',
        'licence': 'https://github.com/Unidata/tds/blob/master/LICENSE',
        'provenance': 'https://ouranosinc.github.io/pavics-sdi/provenance/index.html'
    },
    'monitoring': {
        'ncWMS': {
            'request': {
                'url': 'https://10.0.2.15/twitcher/ows/proxy/thredds/wms/birdhouse/testdata/ta_Amon_MRI-CGCM3_decadal1980_r1i1p1_199101-200012.nc?service=WMS&version=1.3.0&request=GetCapabilities'
            }
        },
    }
}

SERVICES['Thredds'] = {
    'info': {
        'name': 'Thredds',
        'synopsis': 'Climate Data Catalog and Format Renderers',
        'version': "4.6.18-unidata-2022-01",
        'releaseTime': get_release_time_from_repo_tag("docker", "pavics/thredds-docker", "4.6.18-unidata-2022-01"),
        'institution': 'Ouranos',
        'researchSubject': 'Catalog',
        'supportEmail': 'helpdesk@example.com',
        'category': 'Catalog',
        'tags': ['Catalog', 'Climate Data']
    },
    'stats': {
        'method': '.*',
        'route': '/twitcher/ows/proxy/thredds/.*'
    },
    'redirect': {
        'doc': 'https://www.unidata.ucar.edu/software/tds/',
        'releasenotes': 'https://docs.unidata.ucar.edu/tds/current/userguide/upgrade.html',
        'support': 'https://www.unidata.ucar.edu/software/tds/#help',
        'source': 'https://github.com/Unidata/tds',
        'tryme': 'https://10.0.2.15/twitcher/ows/proxy/thredds/',
        'licence': 'https://github.com/Unidata/tds/blob/main/LICENSE',
        'provenance': 'https://downloads.unidata.ucar.edu/tds/'
    },
    "monitoring": {
        "Thredds": {
            'request': {
                'url': 'http://thredds:8080//twitcher/ows/proxy/thredds/catalog.html'
            }
        }
    }
}

CANARIE_STATS_ROUTES.append('thredds')
