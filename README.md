<div align="center">

# aiostreammagic

#### An async python package for interfacing with Cambridge Audio / Stream Magic compatible streamers
[![GitHub Release][releases-shield]][releases]
[![Python Versions][python-versions-shield]][pypi]
[![Downloads][downloads-shield]][pypi]
![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE.md)

</div>

# About
This module implements a Python client for the Stream Magic API used to control Cambridge Audio streamers. The API connects over TCP/IP and supports several streamers, receivers, and pre-amps.

## Supported Devices
- Cambridge Audio Evo 75
- Cambridge Audio Evo 150
- Cambridge Audio CXN
- Cambridge Audio CXN (v2)
- Cambridge Audio CXR120
- Cambridge Audio CXR200
- Cambridge Audio 851N
- Cambridge Audio Edge NQ

If your model is not on the list of supported devices, and everything works correctly then add it to the list by opening a pull request.

# Installation
```shell
pip install aiostreammagic
```

[license-shield]: https://img.shields.io/github/license/noahhusby/aiostreammagic.svg
[downloads-shield]: https://img.shields.io/pypi/dm/aiostreammagic
[python-versions-shield]: https://img.shields.io/pypi/pyversions/aiostreammagic
[maintenance-shield]: https://img.shields.io/maintenance/yes/2024.svg
[releases-shield]: https://img.shields.io/github/release/noahhusby/aiostreammagic.svg
[releases]: https://github.com/noahhusby/aiostreammagic/releases
[pypi]: https://pypi.org/project/aiostreammagic/