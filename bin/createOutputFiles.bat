@ECHO OFF

set /p cfgfile="Enter the sumocfg file: >"
set /p output="Enter the directory for the output files: >"

sumo -c %cfgfile% --emission-output %output%/traceEmission.xml

rem sumo -c %cfgfile% --fcd-output %output%/traceVehiclePosition.xml

rem sumo -c %cfgfile% --lanechange-output %output%/traceLaneChange.xml

rem sumo -c lachine.sumocfg --vtk-output %output%/VTK/trace_vkt.xml
