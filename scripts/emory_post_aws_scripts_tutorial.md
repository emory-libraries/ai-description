

## Emory's AI Post Scripts

### `convert_ai_csv_to_ingest` Prerequisites

 - Ruby must be installed on the computer operating the script. The script has been written and tested with version v3.1.2, but other versions may be compatible, as well.
 - The script utilizes methods that are stored in the `aws_ai_post_processor.rb`. Please download into the same folder that holds the script.
 - The script must be made executable. For Unix-based systems, use the command `chmod +x <filename>`.
 - The CSV output from the AWS AI UI will be passed to the command. The file must be on the same computer and the script accepts the full path to the CSV file.

### `convert_ai_csv_to_ingest`

#### Usage
1. If all requirements are fulfilled above, the script can be kicked off by running `./convert_ai_csv_to_ingest.rb <operating CSV's filename>`. That is assuming that the script and the CSV files are in the same folder that your terminal is currently in.
2. The successful completion of this script will return a different CSV file with the naming convention of `ai_post_processed_ingest_<today's date and time>.csv` within the same folder that the command was processed.

### Errors
Please report any errors that appear Ruby-related to Software Development.
