"""Text search on the metadata database.

Each string is tokenized by converting it to lower case and
splitting it on characters that are not Unicode letters/numbers or a dash.
We currently do not remove diacritics so these will need to be
converted to ASCII by the user.
If a text query involves only non-letter/number/dash characters,
the filter will not be well-defined and will be ignored when
constructing SQL statements.

For convenience, a non-empty character vector may be used in ``query``.
- A list of length 1 is treated as shorthand for a text
query with default arguments in :py:func:`~.define_text_query`.
- A list of length greater than 1 is treated as
shorthand for an `AND` operation on default text queries for
each of the individual strings.

See Also:
    :py:func:`~gypsum_client.fetch_metadata_database.fetch_metadata_database`,
    to download and cache the database files.

    See `here <https://github.com/ArtifactDB/bioconductor-metadata-index>`_,
    for details on the SQLite file contents and table structure.
"""

import json
import re
import sqlite3
from typing import Dict, List, Optional, Union

__author__ = "chatGPT"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

#####
## I'm tired, so used chatGPT to test out its R to Python capabilities.
## It did hallucinate a bit but otherwise did a pretty good job!
#####


class GypsumSearchClause:
    def __init__(
        self,
        type: str,
        text: Optional[str] = None,
        field: Optional[str] = None,
        partial: bool = False,
        children: Optional[List] = None,
        child: Optional[object] = None,
    ):
        self.type = type
        self.text = text
        self.field = field
        self.partial = partial
        self.children = children if children is not None else []
        self.child = child

    def __and__(self, other):
        return GypsumSearchClause(type="and", children=[self, other])

    def __or__(self, other):
        return GypsumSearchClause(type="or", children=[self, other])

    def __invert__(self):
        return GypsumSearchClause(type="not", child=self)


def search_metadata_text(
    path: str,
    query: Union[str, GypsumSearchClause],
    latest: bool = True,
    include_metadata: bool = True,
) -> List[Dict]:
    """Text search on the metadata database.

    Perform a text search on a SQLite database containing
    metadata from the gypsum backend. This is based on a precomputed
    tokenization of all string properties in each metadata document;
    see `here <https://github.com/ArtifactDB/bioconductor-metadata-index>`_
    for details.

    Examples:
        - Search all metadata for a keyword:

        .. code-block:: python

            search_metadata_text(
                sqlite_path,
                ["mikoto"],
                include_metadata=False,
                latest=False
            )

        - Search for metadata containing multiple keywords (`AND` operation):

        .. code-block:: python

            search_metadata_text(
                sqlite_path,
                ["sakugawa", "judgement"],
                include_metadata=False,
                latest=False
            )

        - Search for metadata container either of the keywords (`OR` operation):

        .. code-block:: python

            query = define_text_query("uiharu") | define_text_query("rank")
            result = search_metadata_text(
                sqlite_path,
                query,
                include_metadata=False,
                latest=False
            )

    Args:
        path:
            Path to the SQLite file, usually obtained
            by :py:func:`~gypsum_client.fetch_assets.fetch_metadata`.

        query:
            List of keywords specifying the query to execute.

            May be :py:class:`~.GypsumSearchClause` class generated by
            :py:func:`~.define_text_query`.

        latest:
            Whether to only search in the latest version for each
            asset. Defaults to True.

        include_metadata:
            Whether metadata should be returned.
            Defaults to True.

    Returns:
        Results matching the query.

    """
    where = search_metadata_text_filter(query)
    cond = where["where"]
    params = where["parameters"]

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        stmt = "SELECT versions.project AS project, versions.asset AS asset, versions.version AS version, path"

        if include_metadata:
            stmt += ", json_extract(metadata, '$') AS metadata"

        if not latest:
            stmt += ", versions.latest AS latest"

        stmt += " FROM paths LEFT JOIN versions ON paths.vid = versions.vid"

        if latest:
            cond.append("versions.latest = 1")

        if cond:
            stmt += " WHERE " + " AND ".join(cond)

        cursor = conn.execute(stmt, params)
        results = [dict(row) for row in cursor.fetchall()]
        if include_metadata:
            for result in results:
                result["metadata"] = json.loads(result["metadata"])

        return results
    finally:
        conn.close()


def define_text_query(
    text: str, field: Optional[str] = None, partial: bool = False
) -> GypsumSearchClause:
    """Define a query.

    Args:
        text:
            Text to search by.

        field:
            Name of the metadata field to search by.

            If `None`, search is performed on all metadata fields.

        partial:
            Whether text contains SQLite wild cards for partial matches.

            Defaults to False.

    Returns:
        `GypsumSearchClause` defining the search.
    """
    return GypsumSearchClause(type="text", text=text, field=field, partial=partial)


def search_metadata_text_filter(
    query: Union[str, GypsumSearchClause], pid_name: str = "paths.pid"
) -> Dict[str, Union[str, List]]:
    query = sanitize_query(query)

    if query is None:
        return {"where": [], "parameters": {}}

    env = {"parameters": {}}
    cond = build_query(query, pid_name, env)
    return {"where": cond, "parameters": env["parameters"]}


def sanitize_query(
    query: Union[str, GypsumSearchClause],
) -> Optional[GypsumSearchClause]:
    if isinstance(query, list):
        if len(query) > 1:
            query = GypsumSearchClause(
                type="and", children=[define_text_query(q) for q in query]
            )
        elif len(query) == 1:
            query = define_text_query(query[0])
        else:
            raise ValueError("'query' must have atleast 1 element.")

    if query.type == "not":
        query.child = sanitize_query(query.child)
        if query.child is None:
            return None
        return query

    if query.type != "text":
        query.children = [
            sanitize_query(child)
            for child in query.children
            if sanitize_query(child) is not None
        ]

        if not query.children:
            return None

        if len(query.children) == 1:
            return query.children[0]

        return query

    extras = "%" if query.partial else ""
    text_tokens = re.split(
        r"[^a-zA-Z0-9" + re.escape(extras) + r"-]", query.text.lower()
    )
    text_tokens = [token for token in text_tokens if token]
    if not text_tokens:
        return None

    children = [
        define_text_query(token, field=query.field, partial=query.partial)
        for token in text_tokens
    ]

    if len(children) == 1:
        return children[0]

    return GypsumSearchClause(type="and", children=children)


def add_query_parameter(env: Dict, value: str) -> str:
    param_name = f"p{len(env['parameters'])}"
    env["parameters"][param_name] = value
    return f":{param_name}"


def build_query(query: GypsumSearchClause, name: str, env: Dict) -> List[str]:
    if query.type == "text":
        param_name = add_query_parameter(env, query.text)
        match_str = f"tokens.token {'LIKE' if query.partial else '='} {param_name}"
        if query.field:
            field_param = add_query_parameter(env, query.field)
            return [
                f"{name} IN (SELECT pid FROM links LEFT JOIN tokens ON tokens.tid = links.tid LEFT JOIN fields ON fields.fid = links.fid WHERE {match_str} AND fields.field = {field_param})"
            ]
        return [
            f"{name} IN (SELECT pid FROM links LEFT JOIN tokens ON tokens.tid = links.tid WHERE {match_str})"
        ]

    if query.type == "not":
        return [f"NOT ({build_query(query.child, name, env)[0]})"]

    if query.type == "and":
        return [
            " AND ".join(build_query(child, name, env)[0] for child in query.children)
        ]

    if query.type == "or":
        is_text = [child for child in query.children if child.type == "text"]
        non_text = [child for child in query.children if child.type != "text"]

        text_clauses = []
        for child in is_text:
            param_name = add_query_parameter(env, child.text)
            match_str = f"tokens.token {'LIKE' if child.partial else '='} {param_name}"
            if child.field:
                field_param = add_query_parameter(env, child.field)
                text_clauses.append(f"({match_str} AND fields.field = {field_param})")
            else:
                text_clauses.append(match_str)

        if text_clauses:
            text_query = " OR ".join(text_clauses)
            text_query = f"{name} IN (SELECT pid FROM links LEFT JOIN tokens ON tokens.tid = links.tid WHERE {text_query})"
        else:
            text_query = ""

        non_text_clauses = " OR ".join(
            build_query(child, name, env)[0] for child in non_text
        )

        if len(non_text) > 0:
            return [f"({text_query} OR {non_text_clauses})"]
        else:
            return [f"({text_query})"]

    raise ValueError(f"Unsupported query type: {query.type}")
