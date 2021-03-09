from fastapi import FastAPI, HTTPException, Request
import uvicorn
import libvirt
import sys
from pathlib import Path
import argparse

VERSION = "0.1.0"

parser = argparse.ArgumentParser(
    prog='webvirt', description='A webserver serving a REST-inspired API for managing libvirt virtual machines')

parser.add_argument('--port', type=int,
                    help='port the webserver should bind to', default=5000)

parser.add_argument('--address', type=str,
                    help='address the webserver should bind to', default='0.0.0.0')

ARGS = parser.parse_args()

api = FastAPI(
    title="webvirt",
    description="A REST-inspired API for managing libvirt virtual machines",
    version=VERSION,
)

LIBVIRT_CONN = libvirt.open(None)

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    DEVICES_PATH = Path(sys.executable) / 'devices'
else:
    DEVICES_PATH = Path(__file__).parent / 'devices'


def get_state_string(domain):
    state = domain.state()[0]

    state_strings = [
        '',
        'running',
        'blocked on resource',
        'paused by user',
        'being shutdown',
        'shut off',
        'crashed',
        'suspended by guest power management',
        ''
    ]

    return(state_strings[state])


def xml_method(domain, xml_name, request, attach_or_detach_device):
    dom = LIBVIRT_CONN.lookupByName(domain)

    try:
        template_path = Path(DEVICES_PATH) / ('%s.xml' % xml_name)
        template_xml = Path(template_path).read_text()

        xml = template_xml

        for var, val in request.query_params.items():
            xml = xml.replace('$%s' % var.upper(), val)

        getattr(dom, attach_or_detach_device)(xml)

        return {'device': 'attached', 'xml': xml}

    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail="%s not found" % template_path)
    except libvirt.libvirtError as e:
        raise HTTPException(status_code=422, detail=e.get_error_message())


@api.get(
    "/api/0/state/{domain}",
    summary='Get domain state',
    description="Returns the domain state as a string (see <a href='https://www.libvirt.org/html/libvirt-libvirt-domain.html#virDomainState'>virDomainState</a>)"
)
async def read_item(domain):
    dom = LIBVIRT_CONN.lookupByName(domain)

    return get_state_string(dom)


@api.get(
    "/api/0/start/{domain}",
    summary='Start domain'
)
async def read_item(domain):
    dom = LIBVIRT_CONN.lookupByName(domain)

    if dom.state()[0] == 1:
        return "already running"
    else:
        dom.create()
        return "starting"


@api.get(
    "/api/0/shutdown/{domain}",
    summary='Shutdown domain'
)
async def read_item(domain):
    dom = LIBVIRT_CONN.lookupByName(domain)

    if dom.state()[0] != 1:
        return "not running"
    else:
        dom.shutdown()
        return "shutting down"


@api.get(
    "/api/0/attach/{domain}/{xml_name}",
    summary='Attach host device',
    description='Attach a host device by using an XML template under devices/. Query parameters for variable substitution'
)
async def read_item(domain, xml_name, request: Request):
    xml_method(domain, xml_name, request, 'attachDevice')


@api.get(
    "/api/0/attach/{domain}/{xml_name}",
    summary='Detach host device',
    description='Detach a host device by using an XML template under devices/. Query parameters for variable substitution'
)
async def read_item(domain, xml_name, request: Request):
    xml_method(domain, xml_name, request, 'detachDevice')


@api.get(
    "/api/0/version",
    summary='Get API version',
    description="The API version (see <a href='https://semver.org/'>semantic versioning</a>)"
)
async def get_item():
    return VERSION

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        uvicorn.run(api, host=ARGS.address, port=ARGS.port)
    else:
        uvicorn.run('webvirt:api', host=ARGS.address,
                    port=ARGS.port, reload=True)
