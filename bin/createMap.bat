@ECHO OFF

set /p boundries=Enter the boundries file: 
set /p largeOSM=Enter the large OSM file containg the boundry: 
set /p outputFile=Enter the SUMO net file: 
set sumoplustools=../sumoplustools/

@ECHO ON

python %sumoplustools%ConvertMaps/createPoly.py -g %boundries% -p poly-file.poly
%sumoplustools%ConvertMaps/osmconvert %largeOSM% -B=poly-file.poly -o=osm-file.osm
python %sumoplustools%ConvertMaps/addOSM.py -osm osm-file.osm
netconvert --osm-files osm-file.osm -o %outputFile% --output.street-names=True --output.original-names=True --tls.guess-signals=True --tls.default-type="actuated" --crossings.guess=True