defmodule AppWeb.AssetController do
  use AppWeb, :controller

  alias App.Catalog
  alias App.Catalog.Asset

  def index(conn, _params) do
    assets = Catalog.list_assets()
    render(conn, :index, assets: assets)
  end

  def new(conn, _params) do
    changeset = Catalog.change_asset(%Asset{})
    render(conn, :new, changeset: changeset)
  end

  def create(conn, %{"asset" => asset_params}) do
    case Catalog.create_asset(asset_params) do
      {:ok, asset} ->
        conn
        |> put_flash(:info, "Asset created successfully.")
        |> redirect(to: ~p"/assets/#{asset}")

      {:error, %Ecto.Changeset{} = changeset} ->
        render(conn, :new, changeset: changeset)
    end
  end

  def show(conn, %{"id" => id}) do
    asset = Catalog.get_asset!(id)
    render(conn, :show, asset: asset)
  end

  def edit(conn, %{"id" => id}) do
    asset = Catalog.get_asset!(id)
    changeset = Catalog.change_asset(asset)
    render(conn, :edit, asset: asset, changeset: changeset)
  end

  def update(conn, %{"id" => id, "asset" => asset_params}) do
    asset = Catalog.get_asset!(id)

    case Catalog.update_asset(asset, asset_params) do
      {:ok, asset} ->
        conn
        |> put_flash(:info, "Asset updated successfully.")
        |> redirect(to: ~p"/assets/#{asset}")

      {:error, %Ecto.Changeset{} = changeset} ->
        render(conn, :edit, asset: asset, changeset: changeset)
    end
  end

  def delete(conn, %{"id" => id}) do
    asset = Catalog.get_asset!(id)
    {:ok, _asset} = Catalog.delete_asset(asset)

    conn
    |> put_flash(:info, "Asset deleted successfully.")
    |> redirect(to: ~p"/assets")
  end
end
