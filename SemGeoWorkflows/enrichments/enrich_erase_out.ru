# Typing gis:Erase

# Set of region datasets
INSERT {
	?out ada:hasElement [ ada:hasAttribute [ a gis:Region ] ].
} WHERE{
	?node a gis:Erase;
			wf:output ?out.
	FILTER NOT EXISTS { 
		?out ada:hasElement ?out1.
		?out1 ada:hasAttribute ?out2.
		?out2 a gis:Region. 
	}
}