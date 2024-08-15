defmodule App.Repo.Migrations.CreateAssets do
  use Ecto.Migration

  def change do
    create table(:assets) do
      add :title, :string
      add :domain_id, references(:domains, on_delete: :nothing)

      timestamps(type: :utc_datetime)
    end

    create index(:assets, [:domain_id])
  end
end
