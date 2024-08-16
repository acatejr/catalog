defmodule CrawlersTest do
  use ExUnit.Case
  doctest Crawlers

  test "greets the world" do
    assert Crawlers.hello() == :world
  end

  test "crawls data.gov" do
    assert Crawlers.crawl_data_dot_gov() == :ok
  end
end
