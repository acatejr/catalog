defmodule App.Catalog.Asset do
  use Ecto.Schema
  import Ecto.Changeset

  schema "assets" do
    field :title, :string
    field :domain_id, :id

    timestamps(type: :utc_datetime)
  end

  @doc false
  def changeset(asset, attrs) do
    asset
    |> cast(attrs, [:title])
    |> validate_required([:title])
  end
end
