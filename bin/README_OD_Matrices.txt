
HOW TO GENERATE TRIPS FROM Origin Destination Matrix
    
    - Ensure that an .add.xml file contains the shapes for every taz district:
        - The name for this file should be "taz_shapes.add.xml"
        - There must be a unique ID value for each taz element
        - The shape of the taz district uses simulation coordinates instead of geo coordinates 
    ex:
        <additional>
            <taz id="taz_0" shape="6163.21,3064.91 5691.63,3255.45 5694.01,2660.02 6194.17,2662.40 6163.21,3064.91" color="blue"/>
            <taz id="taz_1" shape="3826.91,3513.36 3148.73,3502.62 3193.46,2819.07 3937.86,2722.44 3826.91,3513.36" color="green"/>
            ... (More taz districts) ...
        </additional>

    - Update the "OD_Matrix.conf.xml" configuration file with references to the OD matrix files:
        - The .taz.xml file must be create using the edges in the district, this is generated from the .add.xml file
        - od-matrix-file can be multiple files, use a ',' between the file names
    ex: 
        <configuration>
            <input>
                <taz-files value="taz_edges.taz.xml"/>
                <od-matrix-files value="OD_Matrices/OD_matrix_0.od,OD_Matrices/OD_matrix_1.od"/>
            </input>
        </configuration>
    
    - Creating an OD Matrix:
        - Refer to the template in "OD_Matrices/OD_matrix_template.od"
    
    - Generate the files using the createODTrips.bat file:
        - Required Files: lachine.net.xml, taz_shapes.add.xml, OD_matrix.conf.xml
        - Will generate the taz_edge.taz.xml file required for the OD_matrix.conf.xml configuration file
        - Will generate the OD_matrix.odtrips.xml trips file that can be used with the .sumocfg application file

    - Generate the trip files manually:
        - Use the command prompt to input the following commands:
        
        python %SUMO_HOME%/tools/edgesindistricts.py -n %SUMO_HOME%/Projects/Lachine/lachine.net.xml -t %SUMO_HOME%/Projects/Lachine/OD2Trips/taz_shapes.add.xml -o %SUMO_HOME%/ Projects/Lachine/OD2Trips/taz_edges.taz.xml
            Generates a taz file where each district is defined by edges (streets) within it
            -n: The SUMO network file
            -t: The taz file defined by its shape
            -o: The output taz file, must have extention .taz.xml

        %SUMO_HOME%/bin/od2trips -c %SUMO_HOME%/Projects/Lachine/OD2Trips/OD_matrix.conf.xml -o %SUMO_HOME%/Projects/Lachine/OD2Trips/OD_matrix.odtrips.xml --vtype "veh_passenger" --prefix "veh"
            Generates the trips for the vehicle type using the districts
            -c: The configuration file for the OD matrix containing the taz data and OD matrices
            -o: The output trip file, use extention .odtrips.xml to differentiate from other trip files
            --vtype: The type of vehicle that will travel the trip
            --prefix: The prefix string for the trip ID, used so different trip files have unique trip IDs
        
    - Assign vehicle class to vehicle ID:
        - After the trip files are created, assign the vtype attribute to a SUMO vehicle class
        - A new tag of vType must be created and have the attributes "id" and "vClass"
        - Attribute "id" is the vtype assigned when creating the trip file
        - Attribute "vClass" is the class interpreted by SUMO to generate the vehicles
    ex:
        <routes>
            <vType id="veh_passenger" vClass="passenger" />
            <trip id="tripID_0" type="veh_passenger" ... />
            ... (More vehicle trips) ...
        </routes>

    - Update the sumocfg file to use SUMO-GUI:
        - In the .sumocfg file the input element, routes-files must be updated to use the new trips
    ex:
        <input>
            <route-files value="OD2Trips/OD_matrix.odtrips.xml"/>
        </input> 