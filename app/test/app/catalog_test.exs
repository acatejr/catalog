defmodule App.CatalogTest do
  use App.DataCase

  alias App.Catalog

  describe "assets" do
    alias App.Catalog.Asset

    import App.CatalogFixtures

    @invalid_attrs %{title: nil, archived: nil}

    test "list_assets/0 returns all assets" do
      asset = asset_fixture()
      assert Catalog.list_assets() == [asset]
    end

    test "get_asset!/1 returns the asset with given id" do
      asset = asset_fixture()
      assert Catalog.get_asset!(asset.id) == asset
    end

    test "create_asset/1 with valid data creates a asset" do
      valid_attrs = %{title: "some title", archived: true}

      assert {:ok, %Asset{} = asset} = Catalog.create_asset(valid_attrs)
      assert asset.title == "some title"
      assert asset.archived == true
    end

    test "create_asset/1 with invalid data returns error changeset" do
      assert {:error, %Ecto.Changeset{}} = Catalog.create_asset(@invalid_attrs)
    end

    test "update_asset/2 with valid data updates the asset" do
      asset = asset_fixture()
      update_attrs = %{title: "some updated title", archived: false}

      assert {:ok, %Asset{} = asset} = Catalog.update_asset(asset, update_attrs)
      assert asset.title == "some updated title"
      assert asset.archived == false
    end

    test "update_asset/2 with invalid data returns error changeset" do
      asset = asset_fixture()
      assert {:error, %Ecto.Changeset{}} = Catalog.update_asset(asset, @invalid_attrs)
      assert asset == Catalog.get_asset!(asset.id)
    end

    test "delete_asset/1 deletes the asset" do
      asset = asset_fixture()
      assert {:ok, %Asset{}} = Catalog.delete_asset(asset)
      assert_raise Ecto.NoResultsError, fn -> Catalog.get_asset!(asset.id) end
    end

    test "change_asset/1 returns a asset changeset" do
      asset = asset_fixture()
      assert %Ecto.Changeset{} = Catalog.change_asset(asset)
    end
  end
end
