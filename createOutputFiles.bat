set /p cont=The following files may take a while to create. Do you wish to continue? (y/n): 

if %cont% == n exit

sumo -c lachine.sumocfg --fcd-output Outputs/traceVehiclePosition.xml

sumo -c lachine.sumocfg --emission-output Outputs/traceEmission.xml

sumo -c lachine.sumocfg --lanechange-output Outputs/traceLaneChange.xml

sumo -c lachine.sumocfg --vtk-output Outputs/VTK/trace_vkt.xml
