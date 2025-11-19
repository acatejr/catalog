# Data Harvesting

The project required input data which comes from the following USFS metadata sources:

1. [FSGeodata Clearing House](data.fs.usda.gov/geodata/edw/datasets.php) - Data collected and managed by Forest Service programs is available in a map service and two downloadable file formats – in a shape file and an ESRI file geodatabase. Metadata is available that describes the content, source, and currency of the data. You can filter the list by the topic categories in the menu at the left to help you find information you are interested in. You can view the feature classes in a single dataset by clicking on the name of the parent dataset at the bottom of the abstract.

2. [Datahub](https://data-usfs.hub.arcgis.com/api/feed/dcat-us/1.1.json) - A U.S. Forest Service configured open data site to help partners and the public discover geospatial data published by the Agency. Used together with user data to create maps, apps and other information products.

3. [Research Data Archive (RDA)](https://www.fs.usda.gov/rds/archive/webservice/datagov) - he FS Research Data Archive offers a catalog of hundreds of research datasets funded by Forest Service Research and Development (FS R&D) or by the Joint Fire Science Program (JFSP). Of special interest, our collection includes long-term datasets from a number of Forest Service Experimental Forests, Ranges, and Watersheds (FS EFRs).

Each of the sources provided metadata in XML or JSON format.  A [command line tool](../src/catalog/cli/cli.py) was written to harvest the metadata from those data sources.

The command line data harvester downloads metadata sources and parses each metadata item into a json object.

```json
{
        "id": "7ce585693437c8f937073065960c398cf2a0aa96ed686ad63264bd9befc129d7",
        "title": "Characterizing Ecoregions and Montane Perennial Watersheds of the Great Basin - Watersheds",
        "description": "Multiple research and management partners collaboratively developed a multiscale approach for assessing the geomorphic sensitivity of streams and ecological resilience of riparian and meadow ecosystems in upland watersheds of the Great Basin to disturbances and management actions. The approach builds on long-term work by the partners on the responses of these systems to disturbances and management actions. At the core of the assessments is information on past and present watershed and stream channel characteristics, geomorphic and hydrologic processes, and riparian and meadow vegetation. In this report, we describe the approach used to delineate Great Basin mountain ranges and the watersheds within them, and the data that are available for the individual watersheds. We also describe the resulting database and the data sources. Furthermore, we summarize information on the characteristics of the regions and watersheds within the regions and the implications of the assessments for geomorphic sensitivity and ecological resilience. The target audience for this multiscale approach is managers and stakeholders interested in assessing and adaptively managing Great Basin stream systems and riparian and meadow ecosystems. Anyone interested in delineating the mountain ranges and watersheds within the Great Basin or quantifying the characteristics of the watersheds will be interested in this report. For more information, visit: https://www.fs.usda.gov/research/treesearch/61573",
        "metadata_source_url": "https://data.fs.usda.gov/geodata/edw/edw_resources/meta/S_USA.Hydro_GrBasin_Watersheds.xml",
        "keywords": [
            "inlandWaters",
            "geoscientificInformation",
            "environment",
            "riparian",
            "fire",
            "geomorphology",
            "meadows",
            "mountain range delineation",
            "Great Basin watershed database",
            "Great Basin watershed characteristics",
            "watershed delineation",
            "climate",
            "species",
            "Great Basin",
            "ecosystem resistance and resilience",
            "hydrology",
            "watersheds"
        ],
        "src": "fsgeodata"
},
```

Each json item is stored in a PostgreSQL database table.  The database table has a vector column that stores each items embeddings.  An item's embeddings are computed using title, description, keywords, and src fields.  The metadata loading process also scan the XML and JSON input for data schema information (entity attribute information).  The schema information is used to enhance the vector searching so that queries about data table names, field names and types... can be processed.  An early version of the data harvesting and importing tool only harvested basic data like title, description and keywords.  [Claude Code](https://www.claude.com/product/claude-code) was used to enhance the code so the harvester would include schema information.

As each item, which is stored as a document in a table named documents, is saved or edited an embedding values are calculated and stored in an embeddings column.  Embeddings values are computed based on the sentence transformier `all-MiniLM-L6-v2`.  The transformer was chosen arbitrarily.  Further exploration into an appropriate transformer should be part of future improvements.
