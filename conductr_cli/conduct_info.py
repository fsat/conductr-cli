from conductr_cli import bundle_utils, conduct_request, conduct_url, license, validation, screen_utils
from conductr_cli.conduct_url import conductr_host
from conductr_cli.license import UNLICENSED_DISPLAY_TEXT
import json
import logging
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT


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
    if args.quiet:
        display_quiet(args, bundles)
    else:
        conductr_license = license.get_license(args)
        display_default(args, conductr_license, bundles)

    return True


def display_default(args, conductr_license, bundles):
    log = logging.getLogger(__name__)

    license_to_display = license.format_license(conductr_license) if conductr_license \
        else UNLICENSED_DISPLAY_TEXT
    log.screen('\n{}\n'.format(license_to_display))

    data = [
        {
            'id': display_bundle_id(args, bundle),
            'name': bundle['attributes']['bundleName'],
            'replications': len(bundle['bundleInstallations']),
            'starting': sum([not execution['isStarted'] for execution in bundle['bundleExecutions']]),
            'executions': sum([execution['isStarted'] for execution in bundle['bundleExecutions']])
        } for bundle in bundles
    ]
    data.insert(0, {'id': 'ID', 'name': 'NAME', 'replications': '#REP', 'starting': '#STR', 'executions': '#RUN'})

    padding = 2
    column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * padding})
    has_error = False
    for row in data:
        has_error |= '!' in row['id']
        log.screen('''\
{id: <{id_width}}{padding}\
{name: <{name_width}}{padding}\
{replications: >{replications_width}}{padding}\
{starting: >{starting_width}}{padding}\
{executions: >{executions_width}}'''.format(**dict(row, **column_widths)).rstrip())

    if has_error:
        log.screen('There are errors: use `conduct events` or `conduct logs` for further information')


def display_quiet(args, bundles):
    log = logging.getLogger(__name__)

    for bundle in bundles:
        log.screen(display_bundle_id(args, bundle))


def display_bundle_id(args, bundle):
    bundle_id = bundle['bundleId'] if args.long_ids else bundle_utils.short_id(bundle['bundleId'])
    has_error_display = '! ' if bundle.get('hasError', False) else ''
    return '{}{}'.format(has_error_display, bundle_id)
