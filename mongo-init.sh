until mongosh --host db --eval "print(\"Waiting for mongo...\")"
do
  sleep 1
done
mongosh --host db --eval "rs.initiate({ _id: \"rs0\", members: [{ _id: 0, host: \"db:27017\" }] });"