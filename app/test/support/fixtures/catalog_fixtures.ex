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
        title: "some title"
      })
      |> App.Catalog.create_asset()

    asset
  end

  @doc """
  Generate a domain.
  """
  def domain_fixture(attrs \\ %{}) do
    {:ok, domain} =
      attrs
      |> Enum.into(%{
        name: "some name"
      })
      |> App.Catalog.create_domain()

    domain
  end
end
