rem To specify files, change file paths that are in quotations to deswired files.

python createPoly.py -g "montreal_boundary.geojson" -p poly-file.poly
osmconvert "large-osm.osm.pbf" -B=poly-file.poly -o=osm-file.osm
python addOSM.py -osm osm-file.osm
netconvert --osm-files osm-file.osm -o "montreal-net.net.xml" --output.street-names=True --output.original-names=True --tls.guess-signals=True --tls.default-type="actuated" --crossings.guess=True