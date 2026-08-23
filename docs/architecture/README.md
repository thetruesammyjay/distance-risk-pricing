# Architecture

The browser calls only the FastAPI public gateway. The gateway orchestrates
routing, risk, demand, pricing, and persistence through in-process boundaries.
Those boundaries can later be extracted without coupling the browser to
internal services.

