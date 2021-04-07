# tap-coosto

This is a [Singer](https://singer.io) tap that produces JSON-formatted data
following the [Singer
spec](https://github.com/singer-io/getting-started/blob/master/SPEC.md).

This tap:

- Pulls raw data from [Coosto](https://in.coosto.com/api1doc)
- Extracts the following resources:
  - Intervention details
  - Comments
- Outputs the schema for each resource
- Incrementally pulls data based on the input state

## Step 1: Create a user

This user needs to have access to the API.

## Step 2: Configure

Create a file called `sample_config.json` in your working directory, following [sample_config.json](sample_config.json). The required parameters are the `username` and `password`. More information about authentication can be found in the [API Reference](https://in.coosto.com/api1doc)

This requires a [sample_state.json](sample_state.json) file to let the tap know from when to retrieve data. For example:

```json
{
  "bookmarks": {
    "intervention_details": {
      "start_date": "2020-01-01"
    },
    "comments": {
      "start_date": "2020-01-01"
    }
  }
}
```

Will replicate transaction data from 2015-01-01.

## Step 3: Install and Run

Create a virtual Python environment for this tap. This tap has been tested with Python 3.7, 3.8 and 3.9 and might run on future versions without problems.

```bash
python -m venv singer-coosto
singer-coosto/bin/python -m pip install --upgrade pip
singer-coosto/bin/pip install git+https://github.com/Yoast/singer-tap-coosto.git
```

This tap can be tested by piping the data to a local JSON target. For example:

Create a virtual Python environment with `singer-json`

```bash
python -m venv singer-json
singer-json/bin/python -m pip install --upgrade pip
singer-json/bin/pip install target-json
```

Test the tap:

```bash
singer-coosto/bin/tap-coosto --state sample_state.json -c sample_config.json | singer-json/bin/target-json >> state_result.json
```

Copyright &copy; 2021 Yoast
