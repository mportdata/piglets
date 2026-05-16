from pydantic import BaseModel

class ProfilingQuery(BaseModel):
    """A single query generated for profiling the database."""

    motivation: str = ""
    query: str = ""

class ProfilingQueries(BaseModel):
    """A list of queries generated for profiling the database."""

    exploratory_queries: list[ProfilingQuery] = []