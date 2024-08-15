defmodule App.CatalogTest do
  use App.DataCase

  alias App.Catalog

  describe "domains" do
    alias App.Catalog.Domain

    import App.CatalogFixtures

    @invalid_attrs %{name: nil}

    test "list_domains/0 returns all domains" do
      domain = domain_fixture()
      assert Catalog.list_domains() == [domain]
    end

    test "get_domain!/1 returns the domain with given id" do
      domain = domain_fixture()
      assert Catalog.get_domain!(domain.id) == domain
    end

    test "create_domain/1 with valid data creates a domain" do
      valid_attrs = %{name: "some name"}

      assert {:ok, %Domain{} = domain} = Catalog.create_domain(valid_attrs)
      assert domain.name == "some name"
    end

    test "create_domain/1 with invalid data returns error changeset" do
      assert {:error, %Ecto.Changeset{}} = Catalog.create_domain(@invalid_attrs)
    end

    test "update_domain/2 with valid data updates the domain" do
      domain = domain_fixture()
      update_attrs = %{name: "some updated name"}

      assert {:ok, %Domain{} = domain} = Catalog.update_domain(domain, update_attrs)
      assert domain.name == "some updated name"
    end

    test "update_domain/2 with invalid data returns error changeset" do
      domain = domain_fixture()
      assert {:error, %Ecto.Changeset{}} = Catalog.update_domain(domain, @invalid_attrs)
      assert domain == Catalog.get_domain!(domain.id)
    end

    test "delete_domain/1 deletes the domain" do
      domain = domain_fixture()
      assert {:ok, %Domain{}} = Catalog.delete_domain(domain)
      assert_raise Ecto.NoResultsError, fn -> Catalog.get_domain!(domain.id) end
    end

    test "change_domain/1 returns a domain changeset" do
      domain = domain_fixture()
      assert %Ecto.Changeset{} = Catalog.change_domain(domain)
    end
  end

  describe "assets" do
    alias App.Catalog.Asset

    import App.CatalogFixtures

    @invalid_attrs %{title: nil}

    test "list_assets/0 returns all assets" do
      asset = asset_fixture()
      assert Catalog.list_assets() == [asset]
    end

    test "get_asset!/1 returns the asset with given id" do
      asset = asset_fixture()
      assert Catalog.get_asset!(asset.id) == asset
    end

    test "create_asset/1 with valid data creates a asset" do
      valid_attrs = %{title: "some title"}

      assert {:ok, %Asset{} = asset} = Catalog.create_asset(valid_attrs)
      assert asset.title == "some title"
    end

    test "create_asset/1 with invalid data returns error changeset" do
      assert {:error, %Ecto.Changeset{}} = Catalog.create_asset(@invalid_attrs)
    end

    test "update_asset/2 with valid data updates the asset" do
      asset = asset_fixture()
      update_attrs = %{title: "some updated title"}

      assert {:ok, %Asset{} = asset} = Catalog.update_asset(asset, update_attrs)
      assert asset.title == "some updated title"
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
