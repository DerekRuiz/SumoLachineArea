@ECHO OFF

set /p cont=The following files may take a while to create. Do you wish to continue? (y/n): 

if %cont% == n exit

set /p cfgfile=Enter the sumocfg file: 


sumo -c %cfgfile% --emission-output Outputs/traceEmission.xml

rem -c %cfgfile% --fcd-output Outputs/traceVehiclePosition.xml

rem sumo -c %cfgfile% --lanechange-output Outputs/traceLaneChange.xml

rem sumo -c lachine.sumocfg --vtk-output Outputs/VTK/trace_vkt.xml
