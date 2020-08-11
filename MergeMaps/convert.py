"""
Enter following command in Command Prompt:
osmconvert large-osm.osm.pbf -B="poly-file.poly" -o=osm-file.osm
netconvert --osm-files "osm-file.osm" -o net-file.net.xml --output.street-names True
"""

poly_file = open("C:/Users/epicb/Documents/GitHub/SumoLachineArea/MergeMaps/montreal2.poly", "w")
poly_file.write("montreal_city\n")

user = input("Use districts (1) or montreal (2) shape")
if 1 in user:
    import xml.etree.ElementTree as ET
    tree = ET.parse("C:/Users/epicb/Documents/GitHub/SumoLachineArea/MergeMaps/montreal.xml")
    root = tree.getroot()
    for place in root.findall(".//fme_LIMADMIN"):

        name = place.find("fme_NOM")
        name_text = name.text
        poly_file.write("%s\n" % name_text)

        geom = place.find("fme_GEOM")
        geom_text = geom.text
        poly = geom_text.replace("MULTIPOLYGON","")
        poly = poly.replace("(","")
        poly = poly.replace(")","")

        for coord in poly.split(","):
            poly_file.write(" %s\n" % coord)
        
        poly_file.write("END\n")
else:
    import json
    with open("C:/Users/epicb/Documents/GitHub/SumoLachineArea/MergeMaps/montreal_boundary.geojson") as f:
        data = json.load(f)

    for lon, lat in data['features'][0]['geometry']['coordinates'][0][0]:
        poly_file.write("\t%f %f\n" % (lon, lat))

    poly_file.write("END")
    poly_file.close()