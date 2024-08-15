defmodule AppWeb.DomainLive.Index do
  use AppWeb, :live_view

  alias App.Catalog
  alias App.Catalog.Domain

  @impl true
  def mount(_params, _session, socket) do
    {:ok, stream(socket, :domains, Catalog.list_domains())}
  end

  @impl true
  def handle_params(params, _url, socket) do
    {:noreply, apply_action(socket, socket.assigns.live_action, params)}
  end

  defp apply_action(socket, :edit, %{"id" => id}) do
    socket
    |> assign(:page_title, "Edit Domain")
    |> assign(:domain, Catalog.get_domain!(id))
  end

  defp apply_action(socket, :new, _params) do
    socket
    |> assign(:page_title, "New Domain")
    |> assign(:domain, %Domain{})
  end

  defp apply_action(socket, :index, _params) do
    socket
    |> assign(:page_title, "Listing Domains")
    |> assign(:domain, nil)
  end

  @impl true
  def handle_info({AppWeb.DomainLive.FormComponent, {:saved, domain}}, socket) do
    {:noreply, stream_insert(socket, :domains, domain)}
  end

  @impl true
  def handle_event("delete", %{"id" => id}, socket) do
    domain = Catalog.get_domain!(id)
    {:ok, _} = Catalog.delete_domain(domain)

    {:noreply, stream_delete(socket, :domains, domain)}
  end
end
