Documentation for the Analytic Data API
RescueTime data is detailed and complicated. The Analytic Data API is targeted at bringing developers the prepared and pre-organized data structures already familiar through the reporting views of www.rescuetime.com. The data is read-only through the webservice, but you can perform any manipulations on the consumer side you want. Keep in mind this is a draft interface, and may change in the future. We do intend to version the interfaces though, so it is likely forward compatible.

The Analytic Data API allows for parameterized access, which means you can change the subject and scope of data, and is especially targeted for developer use. The data can be accessed via the HTTP Query interface in several formats.

The Analytic Data API is presented as a read-only resource accessed by simple GET HTTP queries. This provides maximum flexibility with minimal complexity; you can use the provided API tools, or just research the documented parameters and construct your own queries.

Service Access
The base URL to reach this HTTP query API is:

For connections with an API key: https://www.rescuetime.com/anapi/data
For Oauth2 connections:
https://www.rescuetime.com/api/oauth/data - This is the least restritive url and requires the time_data access scope to be granted by the user when the Oauth2 connection is initially set up.
Restricted Report: https://www.rescuetime.com/api/oauth/overview_data - This url will restricts the output to top level category data only and requires the category_data access scope to be granted by the user when the Oauth2 connection is initially set up.
Restricted Report: https://www.rescuetime.com/api/oauth/category_data - This url will restricts the output to sub-category data only and requires the category_data access scope to be granted by the user when the Oauth2 connection is initially set up.
Restricted Report: https://www.rescuetime.com/api/oauth/productivity_data - This url will restricts the output to productivity data only and requires the productivity_data access scope to be granted by the user when the Oauth2 connection is initially set up.
About restricted reports: Restricted reports may be useful if your application requires a less-granular rollup of the data, such as the category view, but NOT the actual activities themselves. These restricted reports help ensure the user’s privacy, and may be a preferable option when asking them to link their accounts.

Required parameters
key - [ Your API key ] OR access_token - [ the access token from the Oauth2 Connection ]
format - [ 'csv' | 'json' ]
Query Parameters
Primary names are chosen for human reading. The short names are for when GET query length is at a premium. The alias is for understanding roughly how it maps into the language used in reporting views, and our own internal nicknames.

Principle name	Short	Alias	Short	Values	Description
perspective	pv	by	by	[ 'rank' | 'interval' ]	
Consider this the X - axis of the returned data. It is what determines how your data is crunched serverside for ordered return.
rank: (default) Organized around a calculated value, usually a sum like time spent.
interval: Organized around calendar time.
resolution_time	rs	interval	i	[ 'month' | 'week' | 'day' | 'hour' | 'minute' ]	
Default is "hour". In an interval report, the X axis unit. In other words, data is summarizd into chunks of this size. "minute" will return data grouped into five-minute buckets, which is the most granular view available.
restrict_begin	rb			date	
Sets the start day for data batch, inclusive (always at time 00:00, start hour/minute not supported)
Format ISO 8601 "YYYY-MM-DD"
restrict_end	re			date	
Sets the end day for data batch, inclusive (always at time 00:00, end hour/minute not supported)
Format ISO 8601 "YYYY-MM-DD"
restrict_kind	rk	taxonomy	ty	[ 'category' | 'activity' | 'productivity' | 'document' ]

('efficiency' is option when perspective is 'interval')	
Allows you to preprocess data through different statistical engines. The perspective dictates the main grouping of the data, this provides different aspects of that main grouping.
overview: sums statistics for all activities into their top level category
category: sums statistics for all activities into their sub category
activity: sums statistics for individual applications / web sites / activities
productivity: productivity calculation
efficiency: efficiency calculation (not applicable in "rank" perspective)
document: sums statistics for individual documents and web pages
restrict_thing	rt	taxon	tx	name (of category, activity, or overview)	
The name of a specific overview, category, application or website. For websites, use the domain component only if it starts with "www", eg. "www.nytimes.com" would be "nytimes.com". The easiest way to see what name you should be using is to retrieve a list that contains the name you want, and inspect it for the exact names.
restrict_thingy	ry	sub_taxon	tn	name	
Refers to the specific "document" or "activity" we record for the currently active application, if supported. For example, the document name active when using Microsoft Word. Available for most major applications and web sites. Let us know if yours is not.
restrict_source_type				[ 'computers' | 'mobile' | 'offline' ]	
Allows for querying by source device type.
restrict_schedule_id	rsi	schedule_id	s	id (integer id of user's schedule/time filter)	
Allows for filtering results by schedule.
Output Formats
The Analytic Data API supports CSV and JSON output.

csv - layout provides rows of comma separated data with a header for column names at top.
json - returns a JavaScript ready object. It has these properties:
notes = String, a short explanation of the data envelope
row_headers = Array, a label for the contents of each index in a row, in the order they appear in row
rows = Array X Array, an array of data rows, where each row is itself an array described by the row_headers
Example Queries
To request information about the user's productivity levels, by hour, for the date of January 1, 2020:
https://www.rescuetime.com/anapi/data?key=YOUR_API_KEY&perspective=interval&restrict_kind=productivity&interval=hour&restrict_begin=2020-01-01&restrict_end=2020-01-01&format=json
To request a list of time spent in each top level category, ranked by duration, for the date of January 1, 2020:
https://www.rescuetime.com/anapi/data?key=YOUR_API_KEY&perspective=rank&restrict_kind=overview&restrict_begin=2020-01-01&restrict_end=2020-01-01&format=csv