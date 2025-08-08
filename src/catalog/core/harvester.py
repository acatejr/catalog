from catalog.lib.docs import merge_docs
from .crawlers import (
    FSGeodataHarvester,
    DataHubHarvester,
    RDAHarvester,
)

def harvest_fsgeodata():
    """
    Harvests and parses metadata from FS Geodata.

    This function initializes an FSGeodataHarvester instance, downloads the required metadata files,
    parses them, and returns the resulting documents.

    Returns:
        list: A list of parsed FS Geodata metadata documents.
    """
    """Harvest data from FS Geodata."""
    fsgeodata = FSGeodataHarvester()
    fsgeodata.download_metadata_files()
    fsgeodata_documents = fsgeodata.parse_metadata()
    return fsgeodata_documents


def harvest_datahub():
    """
    Harvests metadata documents from a DataHub source.

    This function initializes a DataHubHarvester instance, downloads the necessary metadata files,
    parses them, and returns the resulting documents.

    Returns:
        list: A list of parsed metadata documents from DataHub.
    """

    datahub = DataHubHarvester()
    datahub.download_metadata_files()
    datahub_documents = datahub.parse_metadata()
    return datahub_documents


def harvest_rda():
    """Harvest data from RDA."""
    rda = RDAHarvester()
    rda.download_metadata_files()
    rda_documents = rda.parse_metadata()
    return rda_documents


def harvest_all():
    """
    Harvests data from all sources: FS Geodata, DataHub, and RDA.

    This function calls the harvesting functions for each source, merges the documents,
    and removes duplicates.

    Returns:
        list: A list of merged and deduplicated documents from all sources.
    """

    fsgeodata_documents = harvest_fsgeodata()
    # print(f"Extracted {len(fsgeodata_documents)} items from FS Geodata.")

    datahub_documents = harvest_datahub()
    # print(f"Extracted {len(datahub_documents)} items from DataHub.")

    rda_documents = harvest_rda()
    # print(f"Extracted {len(rda_documents)} items from RDA.")

    all_documents = fsgeodata_documents + datahub_documents + rda_documents
    # print(f"Total documents before merging: {len(all_documents)}")

    documents = merge_docs(all_documents)
    # print(f"Total documents after merging: {len(merged_documents)}")
    # duplicate_documents = find_duplicate_documents(merged_documents)

    return documents
