Search: semantic (Vector database search with no AI interactions)
Command: uv run catalog semantic-search --limit=10 "post-wildfire erosion data." 
Example output:

1. Smoothed raster of wildfire transmission to buildings in the continental United States and Hawaii  0.8295
   Keywords: geoscientificinformation, structure, fire, fire effects on environment, wildlandurban interface, natural resource management  use, forest management, wildfire, wildfire exposure, 
wildfire transmission, wildfire management, united states, continental united states, conterminous united states, alaska, hawaii
2. Data on fluvial suspended-sediment response to wildfire and a major post-fire flood  0.8288
   Keywords: environment, inlandwaters, ecology ecosystems  environment, hydrology watersheds sedimentation, fire, fire effects on environment, postfire erosion, suspended sediment, postfire 
floods, colorado, south fork cache la poudre river, colorado front range, roosevelt national forest
3. Potential recreation displacement by wildfire in Los Padres National Forest, California  0.8176
   Keywords: biota, society, fire, fire ecology, fire effects on environment, environment and people, recreation, natural resource management  use, forest management, recreation displacement, 
california, los padres national forest
4. Pre- and post-fire forest structure and composition photo-interpreted data for four sub-watersheds in Eastern Washington, USA  0.8170
   Keywords: environment, ecology ecosystems  environment, landscape ecology, fire, fire effects on environment, forest  plant health, natural resource management  use, forest management, landscape
management, landscape evaluations, photointerpretation, vegetation attributes, joint fire science program, jfsp, washington, okanoganwenatchee national forest, colville national forest
5. Post-fire field observations across the 2007 Egley Fire in central Oregon  0.8169
   Keywords: biota, fire, fire effects on environment, inventory monitoring  analysis, assessments, burn severity, char, landsat, normalized burn ratio, remote sensing, soils, wildfire, cercocarpus
ledifolius, curlleaf mountain mahogany, pinus ponderosa, ponderosa pine, juniperus occidentalis, western juniper, abies concolor, white fir, joint fire science program, jfsp, oregon
6. Northern New Mexico post-fire refugia data  0.8088
   Keywords: elevation, environment, location, ecology ecosystems  environment, landscape ecology, fire, fire ecology, fire effects on environment, refugial gradient, gaussian kernel, burn 
severity, digital elevation model, terrain analysis, species ordination, generalized additive models, spatial climate, disturbance interactions, rear edge populations, pinus ponderosa, northern new
mexico, cerro grande, dome, la mesa, las conchas
7. Spatial wildfire occurrence data for the United States, 1992-2018 [FPA_FOD_20210617]  0.8086
   Keywords: biota, geoscientificinformation, location, fire, fire detection, wildfire, fire program analysis, united states
8. Spatial wildfire occurrence data for the United States, 1992-2012 [FPA_FOD_20140428]  0.8068
   Keywords: biota, geoscientificinformation, location, fire, fire detection, wildfire, fire program analysis, united states
9. Spatial wildfire occurrence data for the United States, 1992-2013 [FPA_FOD_20150323]  0.8065
   Keywords: biota, geoscientificinformation, location, fire, fire detection, wildfire, fire program analysis, united states
10. Spatial wildfire occurrence data for the United States, 1992-2020 [FPA_FOD_20221014]  0.8064
   Keywords: biota, geoscientificinformation, location, fire, fire detection, wildfire, fire program analysis, united states

---
Search: bot
Prompt: simple
Command: uv run catalog bot-search --bot=verde --prompt=simple --limit=25 "post-wildfire erosion data."

Bot response:
Based on the provided catalog records, here are the relevant results for "post-wildfire erosion data", sorted by similarity score in descending order:

1. Post-wildfire hydrogeomorphic risk management assessment data: 2023 streamflow and precipitation after Grizzly Creek Fire, CO (Similarity: 0.8039687515487899)
2. Measurements of low rates of erosion from forest fuel reduction operations in the Clearwater National Forest, Idaho (Similarity: 0.8023645877838135)
3. Northern New Mexico post-fire refugia data (Similarity: 0.8087716102600098) - Although not directly focused on erosion, this dataset may contain relevant information on post-wildfire landscape 
changes.
4. Data on fluvial suspended-sediment response to wildfire and a major post-fire flood (Similarity: 0.8287656409284105) - This dataset contains information on suspended-sediment response to 
wildfire, which may be related to erosion.

These datasets may provide useful information for studying post-wildfire erosion. However, please note that the similarity scores are relatively low, indicating that the datasets may not be 
directly focused on post-wildfire erosion data.

---

Search: bot
Prompt: discovery
Command: uv run catalog bot-search --bot=verde --prompt=discovery --limit=25 "post-wildfire erosion data." 

Bot response:
Yes, there are datasets related to post-wildfire erosion data. 

Here are the most relevant datasets:
1. **Post-wildfire hydrogeomorphic risk management assessment data: 2023 streamflow and precipitation after Grizzly Creek Fire, CO**: This dataset contains 2023 post-fire hydrologic streamflow and 
precipitation data collected after the Grizzly Creek Fire in Colorado. (Source: Research Data Archive, Similarity score: 0.8039687515487899)
2. **Measurements of low rates of erosion from forest fuel reduction operations in the Clearwater National Forest, Idaho**: This dataset includes data on soil erosion associated with forest fuel 
management activities, such as hand felling, cable logging, and prescribed burning, in the Clearwater National Forest, Idaho. (Source: Research Data Archive, Similarity score: 0.8023645877838135)
3. **Northern New Mexico post-fire refugia data**: This dataset contains spatial data, tabular data, and scripts used to analyze the spatial patterns of refugia and associated plant communities 
following several fires in northern New Mexico. (Source: Research Data Archive, Similarity score: 0.8087716102600098)

These datasets may provide valuable information for studying post-wildfire erosion. However, please note that the similarity scores indicate the relevance of each dataset to the query, with lower 
scores indicating closer matches.

---

Search: bot
Prompt: relationships
Command: uv run catalog bot-search --bot=verde --prompt=relationships --limit=25 "post-wildfire erosion data."

Bot response:
Based on the provided catalog context, I have identified several datasets related to post-wildfire erosion data. 

1. **Post-wildfire hydrogeomorphic risk management assessment data: 2023 streamflow and precipitation after Grizzly Creek Fire, CO**: This dataset contains streamflow and precipitation data 
collected after the Grizzly Creek Fire in Colorado, which can be used to study post-wildfire erosion.
2. **Northern New Mexico post-fire refugia data**: Although not exclusively focused on erosion, this dataset includes data on post-fire refugia and associated plant communities, which can be 
related to erosion patterns.
3. **Data on fluvial suspended-sediment response to wildfire and a major post-fire flood**: This dataset contains tabular streamflow and fluvial suspended-sediment data collected after a wildfire 
and post-fire flood in Colorado, which can be used to study post-wildfire erosion.
4. **Measurements of low rates of erosion from forest fuel reduction operations in the Clearwater National Forest, Idaho**: This dataset contains data on erosion rates after forest fuel reduction 
operations, which can be related to post-wildfire erosion.

These datasets can be used to analyze post-wildfire erosion patterns, hydrogeomorphic risk, and refugia dynamics. However, it is essential to note that the relationships between these datasets and 
post-wildfire erosion data are inferred based on their descriptions and may require further analysis to confirm.

Confidence level: Medium-High (inferred relationships based on dataset descriptions)

No duplicates or gaps in data were identified. However, the datasets may complement each other, providing a more comprehensive understanding of post-wildfire erosion when combined.

---

Search: bot
Prompt: lineage
Command: uv run catalog bot-search --bot=verde --prompt=lineage --limit=25 "post-wildfire erosion data." 

Bot response:
The dataset "Post-wildfire hydrogeomorphic risk management assessment data: 2023 streamflow and precipitation after Grizzly Creek Fire, CO" appears to be relevant to the query about post-wildfire 
erosion data.

Here's a summary of the origin, collection method, processing history, and authoritative source system for this dataset:

* Origin: The dataset was created by the US Forest Service as part of a Joint Fire Science Project (JFSP) to study the hydrogeomorphic response and risks following the Grizzly Creek Fire in 
Colorado.
* Collection method: The data were collected through field observations and measurements of streamflow and precipitation at an existing hydrologic monitoring network at the Grizzly Creek Fire site.
* Processing history: The data were collected in 2023 and processed to create a dataset that includes streamflow and precipitation data, as well as other relevant information such as soil moisture 
and weather conditions.
* Authoritative source system: The dataset is hosted on the US Forest Service's Research Data Archive (RDA) platform, which is the authoritative source system for this dataset.

However, it's worth noting that there is another dataset, "Measurements of low rates of erosion from forest fuel reduction operations in the Clearwater National Forest, Idaho", that may also be 
relevant to the query about post-wildfire erosion data. This dataset contains data on erosion rates and other relevant information collected from a study on forest fuel reduction operations in 
Idaho.

In terms of gaps in lineage information, it appears that the processing history for the "Post-wildfire hydrogeomorphic risk management assessment data" dataset is not fully documented, and there 
may be some uncertainty about the specific methods used to collect and process the data. Additionally, the dataset may not include all relevant information about the study design, data collection 
methods, and data processing procedures.
