defmodule App.Repo.Migrations.AddAssetIdToDomain do
  use Ecto.Migration

  def change do
    alter table("domains") do
      add :asset_id, :integer
    end
  end
end
