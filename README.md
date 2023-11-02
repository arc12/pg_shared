# Data Literacy Playground Shared ("pg_shared")
_This repository contains core code which is used in each of the Playthings AND documentation for Plaything development and deployment/hosting etc. For the time-being, it also documents the core configuration settings (single file applicable to all Playthings) and common elements of the Plaything Specifications (which provide the settings for each instance of a Plaything)._

## Playground Configuration Files
All playthings have a separate configuration folder - named according to the PLAYTHING_NAME variable in the core Plaything Python file (see below) - within a root configuration folder which applies to the whole Playground. The root configuration folder should be located as follows:
- for local development and plain Flask execution, in ../Config relative to the plaything source code folder.
- for Azure Function App execution, in an Azure File Share mounted as /Config.

### Core Configuration
A single file, "core_config.json" in the root configuration folder.

### Plaything Configuration (aka Specification)
The collection of configuration files for how the plaything should be realised is referred to a Specification. There is no default Specification; they must always be defined. Indeed: the expectation is that there will be several Specifications defined in order that the conceptual plaything can be realised across a range of contexts and examples.

The starting point for the specification is a JSON file inside the plaything configuration folder (named according to PLAYTHING_NAME). The __specification id__ is the file-name less the ".json" extension and this file is generically called the "specification core file". This is used to construct URLs, which are of the form: {site name}/{plaything name}/{view}/{specification id}. Each plaything may have one or more views; these are defined in the README for the Plaything.

The specification core file contains the following elements which are common to all playthings:
- enabled
- title
- summary
- data_source = an optional element to indicate where the data used in this specification came from.
- initial_view = the name of a view which is the logical starting point. NB: this is only used from the index page.
- lang = a two-character language indicator (e.g. en, fr, zh) which is used to retrieve suitable words/phrases to use e.g. in the menu. NB: adding new languages requires modifications to the source code.
- detail = a container for plaything-specific specification - see the README for the Plaything.
- menu = an ordered list of the Plaything views which should be included in the menu (see the README for the Plaything for a list of the views).
- asset_map = provides the link from Plaything-defined asset codes to specific files - see the README for the Plaything.

## URL Structure, Parameters, and Index/Validation URLs
URLs which render user-facing views are of the form: {site name}/{plaything name}/{view}/{specification id}.

Two parameters are defined, which can be added as required:
- adding menu=1 will cause a menu to be rendered, according to the __menu__ element in the Specification.
- a tag parameter will be recorded in the activity logs, for example to allow discrimination between logs for different groups of users. Tags should be simple strings of alphanumeric characters.

Example (note the "?" and "&" characters which start and separate parameters): {site name}/{plaything name}/{view}/{specification id}?menu=1&tag=group1

In addition to the user-facing views, the following are available for all Playthings:
- an index page at {site name}/{plaything name} lists all of the enabled Specifications. Each title is a link to the __initial_view__.
- a simple validation page at {site name}/{plaything name}/validation. This shows all of the Specifications, including those which are disabled, and gives a simple indication of key Specification errors such as syntax errors in the JSON file or missing asset entries/files.

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