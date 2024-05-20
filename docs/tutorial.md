# Interacting with the gypsum REST API

## Reading files

`gypsum_client` provides several convenience methods for reading from the **gypsum** bucket:

```python
import gypsum_client as gpc

gpc.list_assets("test-R")
gpc.list_versions("test-R", "basic")
gpc.list_files("test-R", "basic", "v1")

out = gpc.save_file("test-R", "basic", "v1", "blah.txt")
with open(out, 'r') as file:
    print(file.read())

dir = gpc.save_version("test-R", "basic", "v1")
for root, dirs, files in os.walk(dir):
    for name in files:
        print(os.path.join(root, name))
```

We can fetch the summaries and manifests for each version of a project's assets.

```python
gpc.fetch_manifest("test-R", "basic", "v1")
gpc.fetch_summary("test-R", "basic", "v1")
```

We can get the latest version of an asset:

```python
gpc.fetch_latest("test-R", "basic")
```

All read operations involve a publicly accessible bucket so no authentication is required.

## Uploading files

### Basic usage

To demonstrate, let's say we have a directory of files that we wish to upload to the backend.

```python
import tempfile
import os

tmp = tempfile.mkdtemp()

with open(os.path.join(tmp, "foo"), "w") as file:
    file.write("abcdefghijklmnopqrstuvwxyz")

with open(os.path.join(tmp, "bar"), "w") as file:
    file.write("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

with open(os.path.join(tmp, "whee"), "w") as file:
    file.write("\n".join(map(str, range(1, 11))))
```

We run the upload sequence of `start_upload()`, `upload_files()` and `complete_upload()`.
This requires authentication via GitHub, which is usually prompted but can also be set beforehand via `set_access_token()` (e.g., for batch jobs).

```python
try:
    init = gpc.start_upload(
        project=project_name,
        asset=asset_name,
        version=version_name,
        files=[os.path.relpath(f, tmp) for f in os.listdir(tmp)],
        directory=tmp
    )
    gpc.upload_files(init, directory=tmp)
    gpc.complete_upload(init)
except Exception as e:
    gpc.abort_upload(init)  # clean up if the upload fails.
    raise e
```

We can also set `concurrent=` to parallelize the uploads in `upload_files()`.

### Link generation

More advanced developers can use `links=` in `start_upload()` to improve efficiency by deduplicating redundant files on the **gypsum** backend.
For example, if we wanted to link to some files in our `test-R` project, we might do:

```python
init = gpc.start_upload(
    project=project_name,
    asset=asset_name,
    version=version_name,
    files=[],
    links=[
        {"from.path": "lun/aaron.txt", "to.project": "test-R", "to.asset": "basic", "to.version": "v1", "to.path": "foo/bar.txt"},
        {"from.path": "kancherla/jayaram.txt", "to.project": "test-R", "to.asset": "basic", "to.version": "v1", "to.path": "blah.txt"}
    ],
    directory=tmp
)
```

This functionality is particularly useful when creating new versions of existing assets.
Only the modified files need to be uploaded, while the rest of the files can be linked to their counterparts in the previous version.
In fact, this pattern is so common that it can be expedited via `clone_version()` and `prepare_directory_upload()`:

```python
dest = tempfile.mkdtemp()
gpc.clone_version("test-R", "basic", "v1", destination=dest)

# Do some modifications in 'dest' to create a new version, e.g., add a file.
# However, users should treat symlinks as read-only - so if you want to modify
# a file, instead delete the symlink and replace it with a new file.
with open(os.path.join(dest, "BFFs"), "w") as file:
    file.write("Aaron\nJayaram")

to_upload = gpc.prepare_directory_upload(dest)
print(to_upload)
```

Then we can just pass these values along to `start_upload()` to take advantage of the upload links:

```python
init = gpc.start_upload(
    project=project_name,
    asset=asset_name,
    version=version_name,
    files=to_upload['files'],
    links=to_upload['links'],
    directory=dest
)
```

## Changing permissions

Upload authorization is determined by each project's permissions, which are controlled by project owners.
Both uploaders and owners are identified based on their GitHub logins:

```python
gpc.fetch_permissions("test-R")
```

Owners can add more uploaders (or owners) via the `set_permissions()` function.
Uploaders can be scoped to individual assets or versions, and an expiry date may be attached to each authorization:

```python
gpc.set_permissions("test-R", 
    uploaders=[
        {
            "id": "jkanche",
            "until": (datetime.datetime.now() + datetime.timedelta(days=1)).
            .replace(microsecond=0).
            isoformat(),
            "asset": "jays-happy-fun-time",
            "version": "1"
        }
    ]
)
```

Organizations may also be added in the permissions, in which case the authorization extends to all members of that organization.

## Probational uploads

Unless specified otherwise, all uploaders are considered to be "untrusted".
Any uploads from such untrusted users are considered "probational" and must be approved by the project owners before they are considered complete.
Alternatively, an owner may reject an upload, which deletes all the uploaded files from the backend.

```python
gpc.approve_probation("test-R", "third-party-upload", "good")
gpc.reject_probation("test-R", "third-party-upload", "bad")
```

An uploader can be trusted by setting `trusted=True` in `set_permissions()`.
Owners and trusted uploaders may still perform probational uploads (e.g., for testing) by setting `probation=True` in `start_upload()`.

## Inspecting the quota

Each project has a quota that specifies how much storage space is available for uploaders.
The quota is computed as a linear function of `baseline + growth_rate * (NOW - year)`,
which provides some baseline storage that grows over time.

```python
gpc.fetch_quota("test-R")
```

Once the project's contents exceed this quota, all uploads are blocked.
The current usage of the project can be easily inspected:

```python
gpc.fetch_usage("test-R")
```

Changes to the quota must be performed by administrators, see [below](#administration).

## Validating metadata

Databases can operate downstream of the **gypsum** backend to create performant search indices, usually based on special metadata files.
`gypsum_client` provides some utilities to check that metadata follows the JSON schema of some known downstream databases.

```python
schema = gpc.fetch_metadata_schema()
with open(schema, 'r') as file:
    print(file.read())
```

Uploaders can verify that their metadata respects this schema via the `validate_metadata()` function.
This ensures that the uploaded files can be successfully indexed by the database, given that the **gypsum** backend itself applies no such checks.

```python
metadata = {
    "title": "Fatherhood",
    "description": "Luke ich bin dein Vater.",
    "sources": [
        {"provider": "GEO", "id": "GSE12345"}
    ],
    "taxonomy_id": ["9606"],
    "genome": ["GRCm38"],
    "maintainer_name": "Darth Vader",
    "maintainer_email": "vader@empire.gov",
    "bioconductor_version": "3.10"
}

gpc.validate_metadata(metadata, schema)
```

## Administration

Administrators of the **gypsum** instance can create projects with new permissions:

```python
gpc.create_project("my-new-project", 
    owners="jkanche", 
    uploaders=[
        {
            "id": "LTLA", 
            "asset": "aarons-stuff"
        }
    ]
)
```

They can alter the quota parameters for a project:

```python
gpc.set_quota("my-new-project",
    baseline=10 * 2**30,
    growth=5 * 2**30
)
```

## Further Information

Check out:
- The [R/Bioconductor gypsum](https://bioconductor.org/packages/release/bioc/html/gypsum.html) package available on `bioc-release`.
- The gypsum [REST API](https://artifactdb.github.io/gypsum-worker/).
- If you are interested in spinning up your own instance of the API, check out the [gypsum-worker](https://github.com/ArtifactDB/gypsum-worker) GitHub repository.