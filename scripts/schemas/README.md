# Package schemas

These are unmodified snapshots fetched on 2026-11-09 from:

- https://agent-plugins.org/schemas/1.0.0/plugin.schema.json
- https://agent-plugins.org/schemas/1.0.0/mcp.schema.json

Builds validate against these versioned snapshots without fetching schemas from
the network. `openai_package.py` also checks the public listing limits from
[OpenAI's field reference](https://developers.openai.com/plugins/deploy/submission#manifest-fields).

The MCP schema does not allow server `extensions`, but
[OpenAI's authentication reference](https://developers.openai.com/plugins/build/plugins#configure-mcp-authentication)
requires `extensions.com.openai.auth` there. Validation checks the portable MCP
fields against the unmodified schema and checks the OAuth extension separately.
It does not claim that the entire extended document passes the base schema.
