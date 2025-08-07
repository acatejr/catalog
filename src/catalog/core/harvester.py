# import click
# from crawlers import (
#     FSGeodataHarvester,
#     DataHubHarvester,
#     RDAHarvester,
#     merge_docs,
#     find_duplicate_documents,
# )


# @click.group()
# def cli():
#     pass


# def _harvest_fsgeodata():
#     """
#     Harvests and parses metadata from FS Geodata.

#     This function initializes an FSGeodataHarvester instance, downloads the required metadata files,
#     parses them, and returns the resulting documents.

#     Returns:
#         list: A list of parsed FS Geodata metadata documents.
#     """
#     """Harvest data from FS Geodata."""
#     fsgeodata = FSGeodataHarvester()
#     fsgeodata.download_metadata_files()
#     fsgeodata_documents = fsgeodata.parse_metadata()
#     return fsgeodata_documents


# @click.command()
# def harvest_fsgeodata():
#     """
#     Harvests data from the FS Geodata source and outputs the number of extracted items.

#     This function calls the internal `_harvest_fsgeodata` function to retrieve documents from FS Geodata,
#     then prints the total number of items extracted.

#     Returns:
#         None
#     """
#     """Harvest data from FS Geodata."""
#     documents = _harvest_fsgeodata()
#     click.echo(f"Extracted {len(documents)} items from FS Geodata.")


# def _harvest_datahub():
#     """
#     Harvests metadata documents from a DataHub source.

#     This function initializes a DataHubHarvester instance, downloads the necessary metadata files,
#     parses them, and returns the resulting documents.

#     Returns:
#         list: A list of parsed metadata documents from DataHub.
#     """

#     datahub = DataHubHarvester()
#     datahub.download_metadata_files()
#     datahub_documents = datahub.parse_metadata()
#     return datahub_documents


# @click.command()
# def harvest_datahub():
#     """
#     Harvests data from DataHub and prints the number of extracted items.

#     This function calls the internal `_harvest_datahub` function to retrieve documents from DataHub,
#     then prints the total number of items extracted.

#     Returns:
#         None
#     """
#     """Harvest data from DataHub."""
#     documents = _harvest_datahub()
#     print(f"Extracted {len(documents)} items from DataHub.")


# def _harvest_rda():
#     """Harvest data from RDA."""
#     rda = RDAHarvester()
#     rda.download_metadata_files()
#     rda_documents = rda.parse_metadata()
#     return rda_documents


# @click.command()
# def harvest_rda():
#     """Harvest data from RDA."""
#     documents = _harvest_rda()
#     print(f"Extracted {len(documents)} items from RDA.")


# @click.command()
# @click.pass_context
# def harvest_all(ctx):
#     """
#     Harvests documents from multiple sources, merges them, and identifies duplicates.

#     This function performs the following steps:
#     1. Harvests documents from three sources: DataHub, FSGEODATA, and RDA.
#     2. Merges the harvested documents into a single collection.
#     3. Identifies and prints duplicate documents based on their titles.
#     4. Prints the total number of documents before and after merging and deduplication.

#     Args:
#         ctx: Context object containing configuration or runtime information.

#     Returns:
#         None
#     """

#     fsgeodata_docs = _harvest_datahub()
#     datahub_docs = _harvest_fsgeodata()
#     rda_docs = _harvest_rda()

#     documents = fsgeodata_docs + datahub_docs + rda_docs
#     print(f"Total documents extracted: {len(documents)}")

#     documents = merge_docs(fsgeodata_docs, datahub_docs, rda_docs)

#     duplicates = find_duplicate_documents(documents)
#     if duplicates:
#         print(f"Found {len(duplicates)} duplicate documents based on title:")
#         for dup in duplicates:
#             print(f"- {dup['id']}: {dup['title']}, {dup['keywords']}")

#     print(f"{len(documents)} documents after merging and deduplication.")


# cli.add_command(harvest_fsgeodata)
# cli.add_command(harvest_datahub)
# cli.add_command(harvest_rda)
# cli.add_command(harvest_all)


# if __name__ == "__main__":
#     cli()
