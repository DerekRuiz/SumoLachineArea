
set /p cfg="Enter the SUMO configuration file: >"
set /p gui="Do you wish to use the SUMO gui? (y/n) >"

if %gui% == y (
    set sumo=sumo-gui
) else (
    set sumo=sumo
)
%sumo% -c %cfg%