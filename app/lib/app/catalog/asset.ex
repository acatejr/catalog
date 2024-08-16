defmodule App.Catalog.Asset do
  alias App.Catalog.Domain
  use Ecto.Schema
  import Ecto.Changeset

  schema "assets" do
    field :title, :string
    belongs_to :domain, Domain

    timestamps(type: :utc_datetime)
  end

  @doc false
  def changeset(asset, attrs) do
    asset
    |> cast(attrs, [:title, :domain_id])
    |> validate_required([:title])
    # |> validate_required([:title, :domain_id])
  end
end
