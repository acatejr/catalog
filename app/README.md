# App

To start your Phoenix server:

  * Run `mix setup` to install and setup dependencies
  * Start Phoenix endpoint with `mix phx.server` or inside IEx with `iex -S mix phx.server`

Now you can visit [`localhost:4000`](http://localhost:4000) from your browser.

Ready to run in production? Please [check our deployment guides](https://hexdocs.pm/phoenix/deployment.html).

## Learn more

  * Official website: https://www.phoenixframework.org/
  * Guides: https://hexdocs.pm/phoenix/overview.html
  * Docs: https://hexdocs.pm/phoenix
  * Forum: https://elixirforum.com/c/phoenix-forum
  * Source: https://github.com/phoenixframework/phoenix

### Reference  
https://thiagoramos.me/articles/how-to-use-migrations-and-insert-data-with-associations-ecto  
mix phx.gen.schema Accounts.User users username:string email:string full_name:string role:string  
mix phx.gen.schema Blog.Post posts title:string body:text status:string user_id:references:users  

mix phx.gen.live Catalog Domain domains name:string
mix phx.gen.live Catalog Asset assets title:string domain_id:references:domains