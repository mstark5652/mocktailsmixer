Overview
--------
Start up services to start ntdate service and the mocktail software assistant


Install
--------
`sudo mv mocktail.service /etc/systemd/service`
`sudo mv ntdate.service /etc/systemd/service`
`cd /etc/systemd/system`

Enable For Startup
------------------
`sudo systemctl enable ntdate.service`
`sudo systemctl enable mocktail.service`



Systemctl Notes
---------------
* Start Service `sudo systemctl start {x}`
* Stop Service `sudo systemctl stop {x}`
* Enable Service for specified trigger `sudo systemctl enable {x}`