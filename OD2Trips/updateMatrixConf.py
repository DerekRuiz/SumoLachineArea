from xml.etree import ElementTree as ET
import os

if __name__ == "__main__":

    for dirpath, dirnames, filenames in os.walk(os.getcwd()):
        if 'OD_Matrices' in dirnames:
            mainDir = dirpath

    try: mainDir
    except NameError: 
        raise Exception('There is no folder titled OD_Matrices')

    od_matrix_files = os.listdir(mainDir + "/OD_Matrices")
    try:
        od_matrix_files.remove("OD_matrix_template.od")
    except ValueError:
        pass

    if len(od_matrix_files) == 0:
        raise Exception("No files in OD_Matrices folder")
    
    value = ""
    for f in od_matrix_files:
        value += ",OD_Matrices/" + f
    value = value.replace(",","",1)

    conf_file = ET.parse(mainDir + "/OD_matrix.conf.xml")
    root = conf_file.getroot()

    root.find(".//od-matrix-files").set('value', value)

    conf_file.write(mainDir + "/OD_matrix.conf.xml")
