
python addTLSToNodes.py -n "../lachine.net.xml" -c "intersectionsafeux.csv"

netconvert --sumo-net-file "../lachine.net.xml" --node-files "tls.nod.xml" -o "../lachine.net.xml"
