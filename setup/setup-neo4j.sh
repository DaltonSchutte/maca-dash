#! /bin/bash

force_flag=''

while getopts 'f' flag;
do
    case "${flag}" in
        f) force_flag='true' ;;
    esac
done

exp_nodes=26148
exp_edges=130000

get_order () {
	n=$(cypher-shell --user neo4j \
		--password none \
		"MATCH (n) RETURN COUNT(n);")
	n=$(echo "$n" | grep -oE '[0-9]+')
	echo $n
}
get_size () {
	n=$(cypher-shell --user neo4j \
		--password none \
		"MATCH ()-[r]->() RETURN COUNT(r)")
	n=$(echo "$n" | grep -oE '[0-9]+')
	echo $n
}

n_nodes=$(get_order)
n_edges=$(get_size)

if [ $n_nodes -eq $exp_nodes ] && [ $n_edges -eq $exp_edges ] && [ ! $force_flag ];
then
	echo "Graph present, will not attempt to rebuild..."
else
	echo "Graph empty or has unexpected size/order, building..."
	cypher-shell --user neo4j \
		--password none \
		-f ./setup/neo4j-graph-builder.cypher
fi

# Validate proper size and order
n_nodes=$(get_order)
n_edges=$(get_size)

if [ ! $n_nodes -eq $exp_nodes ];
then
	echo "ERROR: Expected $exp_nodes nodes, got $n_nodes"
	exit 2
fi

if [ ! $n_edges -eq $exp_edges ];
then
	echo "ERROR: Expected $exp_edges edges, got $n_edges"
	exit 3
fi
