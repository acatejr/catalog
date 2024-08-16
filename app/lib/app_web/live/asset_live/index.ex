defmodule AppWeb.AssetLive.Index do
  use AppWeb, :live_view

  alias App.Catalog
  alias App.Catalog.Asset

  @impl true
  def mount(_params, _session, socket) do
    # {:ok, stream(socket, :assets, Catalog.list_assets())}
    {:ok, stream(socket, :assets, Catalog.list_assets_with_domains())}
  end

  @impl true
  def handle_params(params, _url, socket) do
    {:noreply, apply_action(socket, socket.assigns.live_action, params)}
  end

  defp apply_action(socket, :edit, %{"id" => id}) do
    socket
    |> assign(:page_title, "Edit Asset")
    |> assign(:asset, Catalog.get_asset!(id))
  end

  defp apply_action(socket, :new, _params) do
    socket
    |> assign(:page_title, "New Asset")
    |> assign(:asset, %Asset{})
  end

  defp apply_action(socket, :index, _params) do
    socket
    |> assign(:page_title, "Listing Assets")
    |> assign(:asset, nil)
  end

  @impl true
  def handle_info({AppWeb.AssetLive.FormComponent, {:saved, asset}}, socket) do
    {:noreply, stream_insert(socket, :assets, asset)}
  end

  @impl true
  def handle_event("delete", %{"id" => id}, socket) do
    asset = Catalog.get_asset!(id)
    {:ok, _} = Catalog.delete_asset(asset)

    {:noreply, stream_delete(socket, :assets, asset)}
  end
end
