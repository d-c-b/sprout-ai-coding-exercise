# To Run the project:

- You will need to have Docker and Docker Compose installed (see [here](https://docs.docker.com/desktop/)))
- Clone the repo and in the root run:
```
    docker compose up --build
```
- This will build and start the docker containers
- The main app will be run on http://127.0.0.1:8000/
    - This will accept POST requests at `/posts/` and expects a body of the form
    ```
    {
        "title": "This is an engaging title",
        "paragraphs": [
            "This is the first paragraph. It contains two sentences. Third senetence here",
            "This is the second parapgraph. It contains two more sentences",
            "Third paraphraph here."
        ]
    }
    ```
- Any posts created using the `/posts` endpoint will be stored in the SQLite database `blog_posts.db` included in the repo
- To run the tests, make sure the project is running and run the following command:
```
docker-compose exec app pytest
```
- Making a POST request to `/retry-unchecked-posts/` will trigger a retry to check any blog post items with a null value for `has_foul_language` and call content model again for them

