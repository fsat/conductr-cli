from conductr_cli import bundle_utils, conduct_request, conduct_url, license, validation, screen_utils
from conductr_cli.conduct_url import conductr_host
from conductr_cli.license import UNLICENSED_DISPLAY_TEXT
import json
import logging
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT


DISPLAY_PADDING = 2


@validation.handle_connection_error
@validation.handle_http_error
def info(args):
    """`conduct info` command"""

    log = logging.getLogger(__name__)
    url = conduct_url.url('bundles', args)
    response = conduct_request.get(args.dcos_mode, conductr_host(args), url, auth=args.conductr_auth,
                                   verify=args.server_verification_file, timeout=DEFAULT_HTTP_TIMEOUT)
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    bundles = json.loads(response.text)
    if args.bundle:
        return display_bundle(args, bundles, args.bundle)
    else:
        return display_all(args, bundles)


def display_bundle(args, bundles, bundle_id_or_name):
    log = logging.getLogger(__name__)

    bundles = filter_bundles_by_id_or_name(bundles, bundle_id_or_name)
    if bundles:
        for bundle in bundles:
            display_bundle_properties(args, bundle)

        return True
    else:
        log.error('Unable to find bundle {}'.format(bundle_id_or_name))
        return False


def display_all(args, bundles):
    if args.quiet:
        display_all_quiet(args, bundles)
    else:
        is_license_success, conductr_license = license.get_license(args)
        display_all_default(args, is_license_success, conductr_license, bundles)

    return True


def display_all_default(args, is_license_success, conductr_license, bundles):
    log = logging.getLogger(__name__)

    if is_license_success:
        license_formatted = license.format_license(conductr_license)
        license_to_display = license_formatted if conductr_license['isLicensed'] \
            else '{}\n{}'.format(UNLICENSED_DISPLAY_TEXT, license_formatted)

        log.screen('{}\n'.format(license_to_display))

    data = [
        {
            'id': display_bundle_id(args, bundle),
            'name': bundle['attributes']['bundleName'],
            'compatibility_version': 'v{}'.format(bundle['attributes']['compatibilityVersion']),
            'roles': ', '.join(sorted(bundle['attributes']['roles'])),
            'replications': len(bundle['bundleInstallations']),
            'starting': sum([not execution['isStarted'] for execution in bundle['bundleExecutions']]),
            'executions': sum([execution['isStarted'] for execution in bundle['bundleExecutions']])
        } for bundle in bundles
    ]
    data.insert(0, {
        'id': 'ID',
        'name': 'NAME',
        'compatibility_version': 'VER',
        'roles': 'ROLES',
        'replications': '#REP',
        'starting': '#STR',
        'executions': '#RUN'
    })

    column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * DISPLAY_PADDING})
    has_error = False
    for row in data:
        has_error |= '!' in row['id']
        log.screen('''\
{id: <{id_width}}{padding}\
{name: <{name_width}}{padding}\
{compatibility_version: >{compatibility_version_width}}{padding}\
{replications: >{replications_width}}{padding}\
{starting: >{starting_width}}{padding}\
{executions: >{executions_width}}{padding}\
{roles: <{roles_width}}'''.format(**dict(row, **column_widths)).rstrip())

    if has_error:
        log.screen('There are errors: use `conduct events` or `conduct logs` for further information')


def display_all_quiet(args, bundles):
    log = logging.getLogger(__name__)

    for bundle in bundles:
        log.screen(display_bundle_id(args, bundle))


def display_bundle_id(args, bundle):
    bundle_id = bundle['bundleId'] if args.long_ids else bundle_utils.short_id(bundle['bundleId'])
    has_error_display = '! ' if bundle.get('hasError', False) else ''
    return '{}{}'.format(has_error_display, bundle_id)


def display_bundle_properties(args, bundle):
    display_bundle_attributes(args, bundle)
    display_bundle_scale(bundle)
    display_bundle_config(bundle)
    display_bundle_installations(bundle)
    display_bundle_executions(bundle)
    import json
    print(json.dumps(bundle, sort_keys=True, indent=2, separators=(',', ': ')))


def display_bundle_attributes(args, bundle):
    display_key_value_table('BUNDLE ATTRIBUTES', [
        ('Bundle Id', display_bundle_id(args, bundle)),
        ('Bundle Name', bundle['attributes']['bundleName']),
        ('System', bundle['attributes']['system']),
        ('System Version', bundle['attributes']['systemVersion']),
        ('Compatibility Version', bundle['attributes']['compatibilityVersion']),
        ('Nr of CPUs', bundle['attributes']['nrOfCpus']),
        ('Memory', bundle['attributes']['memory']),
        ('Disk space', bundle['attributes']['diskSpace']),
        ('Roles', ', '.join(sorted(bundle['attributes']['roles']))),
        ('Bundle Digest', bundle['bundleDigest']),
        ('Configuration Digest', bundle['configurationDigest'] if 'configurationDigest' in bundle else None),
        ('Has Error', 'Yes' if bundle['hasError'] else 'No'),
    ])


def display_bundle_config(bundle):
    pass


def display_bundle_installations(bundle):
    pass


def display_bundle_executions(bundle):
    log = logging.getLogger(__name__)

    display_title_table('BUNDLE EXECUTIONS')

    rows = [
        {
            'endpoint': endpoint_name,
            'host': bundle_execution['host'],
            'is_started': 'Yes' if bundle_execution['isStarted'] else 'No',
            'bind_port': endpoint_details['bindPort'],
            'host_port': endpoint_details['hostPort']
        }
        for bundle_execution in bundle['bundleExecutions']
        for endpoint_name, endpoint_details in bundle_execution['endpoints'].items()
    ]

    rows.insert(0, {
        'endpoint': 'ENDPOINT',
        'host': 'HOST',
        'is_started': 'STARTED',
        'bind_port': 'BIND_PORT',
        'host_port': 'HOST_PORT',
    })
    column_widths = dict(screen_utils.calc_column_widths(rows), **{'padding': ' ' * DISPLAY_PADDING})
    for row in rows:
        log.screen('''\
{endpoint: <{endpoint_width}}{padding}\
{host: <{host_width}}{padding}\
{is_started: >{is_started_width}}{padding}\
{bind_port: >{bind_port_width}}{padding}\
{host_port: >{host_port_width}}'''.format(**dict(row, **column_widths)).rstrip())

    log.screen('')


def display_bundle_scale(bundle):
    display_key_value_table('BUNDLE SCALE', [
        ('Nr of Reschedules', bundle['bundleScale']['nrOfReschedules']),
        ('Scale', bundle['bundleScale']['scale']),
    ])


def display_key_value_table(title, entries):
    log = logging.getLogger(__name__)
    display_title_table(title)

    rows = [{'key': key, 'value': value} for key, value in entries if value is not None]

    column_widths = dict(screen_utils.calc_column_widths(rows), **{'padding': ' ' * DISPLAY_PADDING})
    for row in rows:
        log.screen('''\
{key: <{key_width}}{padding}\
{value: <{value_width}}'''.format(**dict(row, **column_widths)).rstrip())

    log.screen('')


def display_title_table(title):
    log = logging.getLogger(__name__)
    log.screen(title)
    title_separator = ''.join(['-' for x in title])
    log.screen(title_separator)


def filter_bundles_by_id_or_name(bundles, bundle_id_or_name):
    return [
        bundle
        for bundle in bundles
        if has_bundle_name(bundle, bundle_id_or_name) or has_bundle_id(bundle, bundle_id_or_name)
    ]


def has_bundle_name(bundle, bundle_name):
    actual_name = bundle['attributes']['bundleName']
    return actual_name == bundle_name or actual_name.startswith(bundle_name)


def has_bundle_id(bundle, bundle_id):
    actual_bundle_id = bundle['bundleId']
    if actual_bundle_id == bundle_id:
        return True
    else:
        if '-' in actual_bundle_id and '-' in bundle_id:
            actual_bundle_id_parts = actual_bundle_id.split('-')
            actual_bundle_digest = actual_bundle_id_parts[0]
            actual_config_digest = actual_bundle_id_parts[1]

            bundle_id_parts = bundle_id.split('-')
            bundle_digest = bundle_id_parts[0]
            config_digest = bundle_id_parts[1]

            bundle_digest_matches = actual_bundle_digest == bundle_digest or \
                actual_bundle_digest.startswith(bundle_digest)
            config_digest_matches = actual_config_digest == config_digest or \
                actual_config_digest.startswith(config_digest)

            return bundle_digest_matches and config_digest_matches
        else:
            return actual_bundle_id.startswith(bundle_id)
