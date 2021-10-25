# Scottish Gaelic Text Normaliser 

The following project contains the code and resources for the Scottish Gaelic text normalisation project. The repo can be cloned and top level functions will allow you to normalise phrases or whole documents. 

## Installation 

To use the program you will have to clone the repo and install dependencies in a python virtualenvironment using python 3 and above. 

## instructions

``from GaelicTextNormaliser import TextNormaliser``
  
``normaliser = TextNormaliser(from_config="config.yaml")``
  
``normaliser.normalise_doc(doc="Bha rìgh òg Easaidh Ruagh an dèigh dha'n oighreachd fhaotainn da fèin ri mòran àbhachd, ag amharc a mach dè a chordadh ris,'s dè thigeadh r'a nadur.")``

``"Bha rìgh òg Easaidh Ruadh an dèidh dhan oighreachd fhaotainn da fhèin ri mòran àbhachd, ag amharc a-mach dè a chòrdadh ris,'s dè thigeadh ra nàdar."``

Alternatively there is a webapp that can be found at https://www.garg.ed.ac.uk/an_gocair. 

## Acknowledgements 

### Supervision 
The development of An Gocair was supervised by Dr Beatrice Alex whose contributions notably enabled the evaluation of the tool as well as guiding and supporting the research into text normalisation. 

### Scottish Gaelic Lexicon

The lexicon file is provided by Michael Bauer, author and lead collaborator on the Am Faclair Beag Scottish Gaelic dictionary. The lexicon is a reformatted version of the dictionary that makes use of Michael's extensive labelling of traditional Gaelic spellings and common misspellings. The resource is extremely vital for the success of the memory based approach. 

### Rules for Normalisation

The lexical and grammatical rules for normalisation were the result of collaboration between the project leader Dr Will Lamb and Bauer. Lamb and Bauer provided the linguistic rules to be translated into Python code. 

### Scottish Gaelic Part of Speech Tagger 

For further conditioning in the rule based approach, part of speech tags were necessary. The code and models for POS tagging is very kindly provided by Loïc Boizou. The scripts were altered slightly to work within the Python object. 

### Further Acknowledgements

This program was funded by the Data-Driven Innovation Initiative (DDI), delivered by the University of Edinburgh and Heriot-Watt University for the Edinburgh and South East Scotland City Region Deal. DDI is an innovation network helping organisations tackle challenges for industry and society by doing data right to support Edinburgh in its ambition to become the data capital of Europe. The project was delivered by the Edinburgh Futures Institute (EFI), one of five DDI innovation hubs which collaborates with industry, government and communities to build a challenge-led and data-rich portfolio of activity that has an enduring impact.
