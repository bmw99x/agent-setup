# Forge commands — fetching threads and replying

Detect the forge from `git remote get-url origin`. `glab api` has no filter flag; pipe to `jq`.
`glab api` fills `:id` with the current project. Trim before output reaches context.

## Unresolved threads to a file

Output format, one line per thread: `[thread-id] path:line :: text` (first note, newlines collapsed).
Thread-less (general) comments get `-` for path:line.

GitLab:

```bash
glab api --paginate "projects/:id/merge_requests/<iid>/discussions?per_page=100" | jq -r '
  .[] | select(.notes[0].resolvable == true and (.notes | map(select(.resolvable and (.resolved|not))) | length > 0))
  | "[\(.id)] \(.notes[0].position.new_path // "-"):\(.notes[0].position.new_line // "-") :: \(.notes[0].body | gsub("\n"; " "))"
' > "$SCRATCH/threads.txt"
```

GitHub (review threads need GraphQL for resolved state):

```bash
gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){
  reviewThreads(first:100){nodes{id isResolved path line comments(first:1){nodes{databaseId body}}}}}}}' \
  -f o=<owner> -f r=<repo> -F n=<number> | jq -r '
  .data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved|not)
  | "[\(.id)] \(.path):\(.line // "-") :: \(.comments.nodes[0].body | gsub("\n"; " "))"' > "$SCRATCH/threads.txt"
```

Line numbers refer to the commented head SHA. Record the head SHA beside the file and tell agents
to locate code by content, not line.

## Reply to a thread

| GitLab | `glab api -X POST projects/:id/merge_requests/<iid>/discussions/<thread-id>/notes -f body="<text>"` |
|---|---|
| GitHub | `gh api graphql -f query='mutation($t:ID!,$b:String!){addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$t,body:$b}){comment{id}}}' -f t=<thread-id> -f b="<text>"` |

Never call the resolve endpoint / `resolveReviewThread`. The reviewer resolves.
