defmodule AppWeb.DomainLiveTest do
  use AppWeb.ConnCase

  import Phoenix.LiveViewTest
  import App.CatalogFixtures

  @create_attrs %{name: "some name"}
  @update_attrs %{name: "some updated name"}
  @invalid_attrs %{name: nil}

  defp create_domain(_) do
    domain = domain_fixture()
    %{domain: domain}
  end

  describe "Index" do
    setup [:create_domain]

    test "lists all domains", %{conn: conn, domain: domain} do
      {:ok, _index_live, html} = live(conn, ~p"/domains")

      assert html =~ "Listing Domains"
      assert html =~ domain.name
    end

    test "saves new domain", %{conn: conn} do
      {:ok, index_live, _html} = live(conn, ~p"/domains")

      assert index_live |> element("a", "New Domain") |> render_click() =~
               "New Domain"

      assert_patch(index_live, ~p"/domains/new")

      assert index_live
             |> form("#domain-form", domain: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert index_live
             |> form("#domain-form", domain: @create_attrs)
             |> render_submit()

      assert_patch(index_live, ~p"/domains")

      html = render(index_live)
      assert html =~ "Domain created successfully"
      assert html =~ "some name"
    end

    test "updates domain in listing", %{conn: conn, domain: domain} do
      {:ok, index_live, _html} = live(conn, ~p"/domains")

      assert index_live |> element("#domains-#{domain.id} a", "Edit") |> render_click() =~
               "Edit Domain"

      assert_patch(index_live, ~p"/domains/#{domain}/edit")

      assert index_live
             |> form("#domain-form", domain: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert index_live
             |> form("#domain-form", domain: @update_attrs)
             |> render_submit()

      assert_patch(index_live, ~p"/domains")

      html = render(index_live)
      assert html =~ "Domain updated successfully"
      assert html =~ "some updated name"
    end

    test "deletes domain in listing", %{conn: conn, domain: domain} do
      {:ok, index_live, _html} = live(conn, ~p"/domains")

      assert index_live |> element("#domains-#{domain.id} a", "Delete") |> render_click()
      refute has_element?(index_live, "#domains-#{domain.id}")
    end
  end

  describe "Show" do
    setup [:create_domain]

    test "displays domain", %{conn: conn, domain: domain} do
      {:ok, _show_live, html} = live(conn, ~p"/domains/#{domain}")

      assert html =~ "Show Domain"
      assert html =~ domain.name
    end

    test "updates domain within modal", %{conn: conn, domain: domain} do
      {:ok, show_live, _html} = live(conn, ~p"/domains/#{domain}")

      assert show_live |> element("a", "Edit") |> render_click() =~
               "Edit Domain"

      assert_patch(show_live, ~p"/domains/#{domain}/show/edit")

      assert show_live
             |> form("#domain-form", domain: @invalid_attrs)
             |> render_change() =~ "can&#39;t be blank"

      assert show_live
             |> form("#domain-form", domain: @update_attrs)
             |> render_submit()

      assert_patch(show_live, ~p"/domains/#{domain}")

      html = render(show_live)
      assert html =~ "Domain updated successfully"
      assert html =~ "some updated name"
    end
  end
end
