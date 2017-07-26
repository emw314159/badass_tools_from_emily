#
# load useful libraries
#
from neo4j.v1 import GraphDatabase, basic_auth

#
# user settings
#
user = 'neo4j'
password = 'aoeuI111'
input_filename = 'output/cypher_commands.txt'

#
# start Neo4j connection
#
driver = GraphDatabase.driver('bolt://localhost:7687', auth=basic_auth(user, password))
session = driver.session()

#
# run cypher commands
#
f = open(input_filename)
for i, line in enumerate(f):
    line = line.strip()
    session.run(line)
f.close()

session.close()



