defmodule App.Repo.Migrations.CreateAssets do
  use Ecto.Migration

  def change do
    create table(:assets) do
      add :title, :string
      add :archived, :boolean, default: false, null: false

      timestamps(type: :utc_datetime)
    end
  end
end
