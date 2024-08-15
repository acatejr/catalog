defmodule App.Repo.Migrations.CreateDomains do
  use Ecto.Migration

  def change do
    create table(:domains) do
      add :name, :string

      timestamps(type: :utc_datetime)
    end
  end
end
