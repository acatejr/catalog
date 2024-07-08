defmodule App.Catalog.Asset do
  use Ecto.Schema
  import Ecto.Changeset

  schema "assets" do
    field :title, :string
    field :archived, :boolean, default: false

    timestamps(type: :utc_datetime)
  end

  @doc false
  def changeset(asset, attrs) do
    asset
    |> cast(attrs, [:title, :archived])
    |> validate_required([:title, :archived])
  end
end
