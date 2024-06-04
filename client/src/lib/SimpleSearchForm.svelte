<script>
    import axios from 'axios'

    let data = []
    let searchTerm = ""
    let baseApiUrl = "http://127.0.0.1:8000/"

    const handleSearch = async(url) => {
        axios.get(url, {
            methid: "GET",
            mode: "no-cors",
            headers: {
                // "Access-Control-Allow-Origin" : "*",
                // "Access-Control-Allow-Methods":"GET,PUT,POST,DELETE,PATCH,OPTIONS",
                "Content-Type": "application/json",
                "X-API-KEY": "api-key",
            }
        })
        .then((resp) => {
            data = resp.data
        })
    }

    const handleInput = async(e) => {
        searchTerm = e.target.value

        if (searchTerm.length > 3) {
            let url = `${baseApiUrl}catalog/api/documents/${searchTerm}/`
            await handleSearch(url)
        } else {
            data = []
        }
    }

</script>

<main>
    <div class="row">
        <div class="col">
            <h3>Simple Catalog Search</h3>
        </div>
    </div>

    <div class="row">
        <div class="col">
            <form>
                <div class="form-group">
                    <input id="search-term" type="text" class="form-control" on:input={handleInput}/>
                </div>
            </form>
        </div>
    </div>

    <br />

    <div class="row">
        <div class="col">
            Search term: {searchTerm}
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Search results:</th>
                    </tr>
                </thead>

                <tbody>
                    {#each data as doc, i}
                        <tr>
                            <td>{doc.description}</td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    </div>
</main>

<style></style>