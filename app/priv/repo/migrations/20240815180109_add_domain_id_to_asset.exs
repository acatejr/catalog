defmodule App.Repo.Migrations.AddDomainIdToAsset do
  use Ecto.Migration

  def change do
    alter table("assets") do
      add :domain_id, :integer
    end
  end
end
