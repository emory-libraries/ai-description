## Emory's AI Scripts

### `extract_aws_pages` and `extract_aws_files_to_csv` Prerequisites

 - Ruby must be installed on the computer operating the script. The scripts have been written and tested with version v3.1.2, but other versions may be compatible, as well.
 - An additional Ruby gem should be installed after Ruby: `faraday`. This can be installed by running `gem install faraday`.
 - Both scripts utilize methods that are stored in the `aws_ai_csv_processor.rb`. Please download into the same folder that house either/both scripts.
 - Either script must be made executable. For Unix-based systems, use the command `chmod +x <filename>`.
 - Since these scripts communicate with Curate production's Solr instance, being on Emory's VPN is required.

### `extract_aws_pages`

#### Prerequisites
This script takes Work ID strings, finds all page images contained within those Works, and produces a CSV file that is ready to process within the AWS AI UI. This script operates on a CSV file that must contain the field `work_id` for all rows. The values must be Curate production Work ID strings that contain 10 alphanumeric characters followed by the `-cor` sub-string. If this field doesn't exist within the CSV given, but the field `work_link` does, these IDs can be extracted from those links. The non-required fields in the operating CSV are `file_set_id`, `work_link`, `file_set_link`, `collection_link`, `notes_from_elizabeth`, `page_context_from_elizabeth`, and `category_from_elizabeth`.

#### Usage
1. If all requirements are fulfilled above, the script can be kicked off by running `./extract_aws_pages.rb <operating CSV's filename>`. That is assuming that the script and the CSV files are in the same folder that your terminal is currently in.
2. The successful completion of this script will return a different CSV file with the naming convention of `aws_ai_<today's date and time>.csv` within the same folder that the command was processed.


### `extract_aws_files_to_csv`

#### Prerequisites
This script takes Work and FileSet ID strings, finds the indicated page images contained within those Works, and produces a CSV file that is ready to process within the AWS AI UI. This script operates on a CSV file that must contain the fields `work_id` and `file_set_id` for all rows. The values must be Curate production ID strings that contain 10 alphanumeric characters followed by the `-cor` sub-string. If these fields don't exist within the CSV given, but the fields `work_link` and `file_set_link` do, these IDs can be extracted from those links. The non-required fields in the operating CSV are `work_link`, `file_set_link`, `collection_link`, `notes_from_elizabeth`, `page_context_from_elizabeth`, and `category_from_elizabeth`.


#### Usage
1. If all requirements are fulfilled above, the script can be kicked off by running `./extract_aws_files_to_csv.rb <operating CSV's filename>`. That is assuming that the script and the CSV files are in the same folder that your terminal is currently in.
2. The successful completion of this script will return a different CSV file with the naming convention of `aws_ai_<today's date and time>.csv` within the same folder that the command was processed.

### Errors
Please report any errors that appear Ruby-related to Software Development.
