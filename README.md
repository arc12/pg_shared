# Data Literacy Playground Shared ("pg_shared")
_This repository contains core code which is used in each of the Playthings AND documentation for Plaything development and deployment/hosting etc. For the time-being, it also documents the core configuration settings (single file applicable to all Playthings) and common elements of the Plaything Specifications (which provide the settings for each instance of a Plaything)._

__Refer to "Plaything Configuration.md" for information on the content of configuration files"; the notes here are developer-focussed.__

## Playground Configuration Files
All playthings have a separate configuration folder - named according to the PLAYTHING_NAME variable in the core Plaything Python file (see below) - within a root configuration folder which applies to the whole Playground. The root configuration folder should be located as follows:
- for local development and plain Flask execution, in ../Config relative to the plaything source code folder.
- for Azure Function App execution, in an Azure File Share mounted as /Config.

### Core Configuration
A single file, "core_config.json" in the root configuration folder. This applies to all deployed Playthings

## Code Organisation and Naming Conventions and Relationship to Runtime/Deployment Options
_The following assumes that VSCode is used._  
The organisation of code for each Plaything is firmly rooted in the principle that each should support independent development and deployment while adopting some design points which will facilitate multi-plaything deployment.

The intention is that each plaything can be executed as a normal Flask App would be, during development (run/debug definition in .vscode/launch.json). Although the Plaything may include a Plotly Dash "app", this is arranged to run within a parent Flask server.

The ultimate deployment target is Microsoft Azure, specifically one or more Function Apps. The as-is structure of each Plaything repository supports deployment of that plaything as a single Function. Although it is possible to deploy different Playthings to the same Function App, the deployment process over-writes the Function App's functions each time, so only one Plaything is actually deployed. This is a consequence of Azure. The option of putting all Playthings into a single repository has been considered and rejected; independence of development and deployment is desired. The intended approach, which is not yet realised, is to write a Python script which will assemble the required parts of several Playthings into a single deployment zip file for deployment using the Azure CLI. Adopting the file-naming convention below will assist this, in particular, __the avoidance of name collisions of the specificed files and folders__. It may, of course, be preferable to use a separate Function App for each Plaything, which is the as-is state of affairs.

Playthings have repository and root folder names of the form "name-part-pt", e.g. "hello-world-pt". These are the projects (aka folders) in VSCode, and generally there will be several, along with the config folder etc, as a VSCode Workspace. Within each Plaything root folder, there should be:
- a pg_shared folder containing the contents of this repo and set up as a git submodule. Once a new repo for a new Plaything exists, simply `git submodule add git@github.com:arc12/pg_shared.git` in its root.
- a folder containing Flask routes and Dash app code, named NamePartFlask e.g. HelloWorldFlask. Files within this should be named consistently between Playthings (see below); except for Dash apps, this means using the same file names and partitioning code similarly.
- a folder named like NamePartFunction e.g. HelloWorldFunction. This provides the hook/specification for a single Azure Function and has minimal content: function.json and \__init__.py. These will require only a small a tweak for each Plaything.
- a file which contains core Plaything setup, with name formed as name_part.py, e.g. hello_world.py. This is imported by the Flask folder's \__init__.py and each Dash app.

It is convenient to place a single venv in the parent folder of Playthings and to share it between them. Deployment of several Functions to a single Function App involves a shared environment.