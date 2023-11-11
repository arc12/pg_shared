# Plaything Configuration
## Plaything Specifications - Common Elements
The collection of configuration files for how the plaything should be realised is referred to a Specification. There is no default Specification; they must always be defined. Indeed: the expectation is that there will be several Specifications defined in order that the conceptual plaything can be realised across a range of contexts and examples.

The documentation concerning the format of the Specification for each kind of plaything is split into two parts; this document describes those elements which are common to all Playthings while a separate README document for each Plaything describes its particular additions. That document declares the formal "plaything name" and this is used as the name of the configuration folder which will be used. This folder may contain many Specifications.

The starting point for each specification is a JSON file inside the plaything configuration folder. The __specification id__ is the file-name less the ".json" extension and this file is generically called the "specification core file". This is used to construct URLs, which are of the form: {site name}/{plaything name}/{view}/{specification id}. Each plaything may have one or more views; these are defined in the README for the Plaything.

The specification core file contains the following elements which are common to all playthings:
- enabled (value is true or false)
- title
- summary
- data_source = an optional element to indicate where the data used in this specification came from (e.g. web address, citation, acknowledgement)
- initial_view = the name of a view which is the logical starting point. NB: this is only used from the index page.
- lang = a two-character language indicator (e.g. en, fr, zh) which is used to retrieve suitable words/phrases to use e.g. in the menu. NB: adding new languages requires modifications to the source code.
- detail = a container for plaything-specific specification - see the README for the Plaything.
- menu = an ordered list of the Plaything views which should be included in the menu (see the README for the Plaything for a list of the views).
- asset_map = provides the link from Plaything-defined asset codes (these are defined in the software) to specific files located inside a sub-folder, "assets". See the README for the Plaything for details of the file and the required and optional asset codes. The same file may be used by any number of Specifications.

## URL Structure, Parameters, and Index/Validation URLs
URLs which render user-facing views are of the form: {site name}/{plaything name}/{view}/{specification id}.

Two parameters are defined, which can be added as required:
- adding menu=1 will cause a menu to be rendered, according to the __menu__ element in the Specification.
- a tag parameter will be recorded in the activity logs, for example to allow discrimination between logs for different groups of users. Tags should be simple strings of alphanumeric characters.

Example (note the "?" and "&" characters which start and separate parameters): {site name}/{plaything name}/{view}/{specification id}?menu=1&tag=group1

In addition to the user-facing views, the following are available for all Playthings:
- an index page at {site name}/{plaything name} lists all of the enabled Specifications. Each title is a link to the __initial_view__.
- a simple validation page at {site name}/{plaything name}/validation. This shows all of the Specifications, including those which are disabled, and gives a simple indication of key Specification errors such as syntax errors in the JSON file or missing asset entries/files.
