defmodule App.CatalogFixtures do
  @moduledoc """
  This module defines test helpers for creating
  entities via the `App.Catalog` context.
  """

  @doc """
  Generate a asset.
  """
  def asset_fixture(attrs \\ %{}) do
    {:ok, asset} =
      attrs
      |> Enum.into(%{
        archived: true,
        title: "some title"
      })
      |> App.Catalog.create_asset()

    asset
  end
end
