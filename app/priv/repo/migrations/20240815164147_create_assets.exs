defmodule App.Repo.Migrations.CreateAssets do
  use Ecto.Migration

  def change do
    create table(:assets) do
      add :title, :string

      timestamps(type: :utc_datetime)
    end
  end
end
