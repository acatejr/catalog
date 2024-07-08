defmodule AppWeb.AssetHTML do
  use AppWeb, :html

  embed_templates "asset_html/*"

  @doc """
  Renders a asset form.
  """
  attr :changeset, Ecto.Changeset, required: true
  attr :action, :string, required: true

  def asset_form(assigns)
end
