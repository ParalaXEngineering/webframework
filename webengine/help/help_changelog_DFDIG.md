# Bugs
Please see https://git.hgeurope.com/defnder-mk2/hw/tools/oufnis/-/issues to report and list issues

# Changelog
## Version 1.4.0
- New display logic
- CAMO support
- On target running support
- Add first steps of log parsing logic

## Version 1.3.5
- Add In LRU Tools the possibility to overright the SIGHT S/N.

## Version 1.3.4
- Small bug improvment
- add AZA and ELA independant programming in the Commissionning workflow

## Version 1.3.2
- Add reprogrammation Satelite 1 Only on motor
- Add PPU and HMI independant programming in the Commissionning workflow
- fix os-only step in commissionning workflow
- fix update folder missing for commissionning

## Version 1.3.1
- Fix motor programmation

## Version 1.3.0
- Update mazer template to version 2.0.3
- Use vertical navbar from mazer template
- Added support for workflows
- Added support for motor reprog
- Corrected 100% CPU usage with SSH
- Prevent reloading page when changing target, and block target change when there is an ongoing operation
- Prevent some action if the target is not valid
- Improved reliability of javascript
- Add new documentation system based on sphynx
- New folder structure

## Version 1.2.0
- Update mazer template to version 2.0.2
- Added user page load detection in order to send data refresh only when the client browser is ready (usefull for dead-slow DSI computers...)
- Added support for changing value of inputs without reloading the page

## Version 1.1.2
- Performance improvement for console reading
- Fixed version check

## Version 1.1.1
- Add a tool to log the temperature of HMI and PPU
- Bug corection for coremark and glxgears
- Add Iperf testing for the fiber
- Double check the program file for full updates

## Version 1.1
- Enhancement to platform in order to better isolate OuFNis function from the core website functions, which allows to create multiple websites from the same platform
- UI polishing
- Website update from server
- Website status checker
- Add modal component, and remote terminal view
- Configuration of authorization in parameters
- Dev example + update documentation

## Version 1.0.2
- Changelog page in markdown
- Use a .exe version of the test bench

## Version 1.0.1
- Correction of a bug when uploading industrial code on the MCU
- Correction of a failing git import when git is not present

## Version 1.0
Initial public release
