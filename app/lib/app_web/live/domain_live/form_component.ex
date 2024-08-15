defmodule AppWeb.DomainLive.FormComponent do
  use AppWeb, :live_component

  alias App.Catalog

  @impl true
  def render(assigns) do
    ~H"""
    <div>
      <.header>
        <%= @title %>
        <:subtitle>Use this form to manage domain records in your database.</:subtitle>
      </.header>

      <.simple_form
        for={@form}
        id="domain-form"
        phx-target={@myself}
        phx-change="validate"
        phx-submit="save"
      >
        <.input field={@form[:name]} type="text" label="Name" />
        <:actions>
          <.button phx-disable-with="Saving...">Save Domain</.button>
        </:actions>
      </.simple_form>
    </div>
    """
  end

  @impl true
  def update(%{domain: domain} = assigns, socket) do
    {:ok,
     socket
     |> assign(assigns)
     |> assign_new(:form, fn ->
       to_form(Catalog.change_domain(domain))
     end)}
  end

  @impl true
  def handle_event("validate", %{"domain" => domain_params}, socket) do
    changeset = Catalog.change_domain(socket.assigns.domain, domain_params)
    {:noreply, assign(socket, form: to_form(changeset, action: :validate))}
  end

  def handle_event("save", %{"domain" => domain_params}, socket) do
    save_domain(socket, socket.assigns.action, domain_params)
  end

  defp save_domain(socket, :edit, domain_params) do
    case Catalog.update_domain(socket.assigns.domain, domain_params) do
      {:ok, domain} ->
        notify_parent({:saved, domain})

        {:noreply,
         socket
         |> put_flash(:info, "Domain updated successfully")
         |> push_patch(to: socket.assigns.patch)}

      {:error, %Ecto.Changeset{} = changeset} ->
        {:noreply, assign(socket, form: to_form(changeset))}
    end
  end

  defp save_domain(socket, :new, domain_params) do
    case Catalog.create_domain(domain_params) do
      {:ok, domain} ->
        notify_parent({:saved, domain})

        {:noreply,
         socket
         |> put_flash(:info, "Domain created successfully")
         |> push_patch(to: socket.assigns.patch)}

      {:error, %Ecto.Changeset{} = changeset} ->
        {:noreply, assign(socket, form: to_form(changeset))}
    end
  end

  defp notify_parent(msg), do: send(self(), {__MODULE__, msg})
end
