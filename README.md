webvirt is a webserver that serves a REST-inspired API for managing libvirt virtual machines. The initial development will be focused on features particularly useful to those running a gaming virtual machine with VFIO. 

# Usage
To run the server simple execute the binary on the same machine that is running libvirt. `./webvirt -h` will show the command-line options for the server.

**DO NOT RUN THIS ON A PUBLIC-FACING PORT!** As it stands, webvirt has no authentication or authorization built in. It is recommended to only expose webvirt to a trusted local network. If you really need authentication or authorization, use a web server with proper middleware. 

# Documentation
The full documentation for the latest version (master branch) can be seen at https://joe-p.github.io/webvirt-redoc/.

Since webvirt is built with FastAPI, the full documentation for the version you are running is accessible at `/docs` (Swagger UI) or `/redoc` (ReDoc). For example, with the default port/address: `http://localhost:5000/docs`.

## Endpoints

Method | Endpoint | Action
--- | --- | ---
GET | /api​/0​/state​/{domain} | Get domain state
GET | /api​/0​/start​/{domain} | Start domain
GET | ​/api​/0​/shutdown​/{domain} | Shutdown domain
GET | /api​/0​/attach​/{domain}​/{xml_name} | Attach host device
GET | /api​/0​/detach​/{domain}​/{xml_name} | Detach host device
GET | /api​/0​/version | Get API version

### Attach and Detach

Most endpoints are rather self-explanatory, with the exception of the attach and detach endpoints. When running webvirt, there should be a directory next to the binary (or python file) named `devices/`. This directory contains XML files that are used to define host devices to be attached. They work the same as they do with libvirt normally with one exception; an XML file under `devices/` can contain variables which start with a '$' and contain all uppercase letters. The values for these variables are set by the query parameters of the GET request.

#### Example
With the following `usb.xml` file:
```xml
<hostdev mode='subsystem' type='usb' managed='yes'>
    <source>
        <vendor id='0x$VENDOR_ID'/>
        <product id='0x$PRODUCT_ID'/>
    </source>
</hostdev>
```

A GET request to `/api/0/attach/{domain}/usb?vendor_id=1234&product_id=5678` would attach the following device:

```xml
<hostdev mode='subsystem' type='usb' managed='yes'>
    <source>
        <vendor id='0x1234'/>
        <product id='0x5678'/>
    </source>
</hostdev>
```

If you wanted to create an endpoint for this specific USB device (without any variables), simple create a new xml file such as `devices/specific_usb_device.xml` with the following contents:

```xml
<hostdev mode='subsystem' type='usb' managed='yes'>
    <source>
        <vendor id='0x1234'/>
        <product id='0x5678'/>
    </source>
</hostdev>
```

Then to attach this device, simple make a GET request to `/api/0/attach/{domain}/specific_usb_device`


#### Variable Names 

Variable names are arbitrary and can be anything (although they should be URI-safe). For example:

`devices/pci_with_rom.xml`:
```xml
<hostdev mode='subsystem' type='pci' managed='yes'>
  <source>
     <address domain='0x$DOMAIN' bus='0x$BUS' slot='0x$SLOT' function='0x$FUNCTION'/>
     <rom file="$ARBITRARY_VARIABLE_NAME"/>
  </source>
</hostdev>
```

Then to attach this device, make a `GET` request to `/api/0/attach/{domain}/pci_with_rom?domain=0000&bus=0f&slot=00&function=0&arbitrary_variable_name=%2Fusr%2Fshare%2Fvgabios%2F1080ti-patched.rom`

Which attaches the following device:
```xml
<hostdev mode='subsystem' type='pci' managed='yes'>
  <source>
     <address domain='0x0000' bus='0x0f' slot='0x00' function='0x0'/>
     <rom file="/usr/share/vgabios/1080ti-patched.rom"/>
  </source>
</hostdev>
```

It should be noted that the variable names in the XML file **must** be all uppercase, but the query parameters are case insensitive.


# Development

Since webvirt is still in early development, suggestions and PRs are very welcomed. There has been no test framework implemented for webvirt (yet), but please provide some manual test results when submitting a PR. 

## Semantic Versioning

webvirt follows [semantic versioning](https://semver.org/):

```
Given a version number MAJOR.MINOR.PATCH, increment the:

1. MAJOR version when you make incompatible API changes,
2. MINOR version when you add functionality in a backwards compatible manner, and
3. PATCH version when you make backwards compatible bug fixes.
Additional labels for pre-release and build metadata are available as extensions to the MAJOR.MINOR.PATCH format.
```

At MAJOR version 0, anything is subject to change, even incompatible API changes.


## Building with PyInstaller

To build a single-file executable with PyInstaller, run `pyinstaller -F webvirt.spec`

If you need to generate a new spec file, run `pyinstaller -F webvirt.py --hidden-import uvicorn.logging --hidden-import uvicorn.loops --hidden-import uvicorn.loops.auto --hidden-import uvicorn.protocols --hidden-import uvicorn.protocols.http --hidden-import uvicorn.protocols.http.auto --hidden-import uvicorn.protocols.websockets --hidden-import uvicorn.protocols.websockets.auto --hidden-import uvicorn.lifespan --hidden-import uvicorn.lifespan.on`

## PEP 8 Style Guide

Source code in this project should adhere to the [PEP 8 style guide](https://www.python.org/dev/peps/pep-0008/).
