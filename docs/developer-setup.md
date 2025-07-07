# Setting up for development

There is a very basic wagtail app in `./example_project` that can be used to test the package output locally.

Clone the package to your computer from GitHub [wagtail-unveil](https://github.com/wagtail-packages/wagtail-unveil#) and chnage into the directory your cloned the package to.

## To install the package and dependencies

UV is recommended for setting up the virtual environment and installing the package dependencies. <https://github.com/astral-sh/uv>

Run the following commands:

```bash
uv sync
source .venv/bin/activate
python manage.py migrate
```

Create a superuser for the app so you can log in to the admin interface:

```bash
python manage.py createsuperuser
```

Set the hostname and port via Admin>Settings>Sites for local testing to `localhost:8000`. The values are used to construct the absolute URLs in the output.

Run the command to see the output:

```bash
python manage.py list_admin_urls
```

## Testing against another wagtail app

You can test the package against another Wagtail app. First, you need to install the package and dependencies and activate the virtual environment inside the wagtail-unveil directory:

```bash
uv sync
source .venv/bin/activate
```

The wagtail bakery demo is a good choice: <https://github.com/wagtail/bakerydemo>

We'll follow the instructions in the README to set up the app using the [virtual environment](https://github.com/wagtail-packages/bakerydemo-wagtail-unveil?tab=readme-ov-file#setup-with-virtualenv) method.

Where the README says to run `pip install -r requirements/development.txt`, you can instead run:

```bash
uv pip install -r requirements/development.txt
```

Then run the following commands to set up the database and initial data:

```bash
uv run python manage.py migrate
uv run python manage.py load_initial_data
```

Add the `wagtail_unveil` package to the `INSTALLED_APPS` list in `bakerydemo/settings/base.py`:

```python
INSTALLED_APPS = [
    ...
    'wagtail_unveil',
    ...
]
```

Run the command `uv run python manage.py list_admin_urls` to see the output of the command. It should list the bakerydemo  admin URLs.

## Configuration options

You can configure the package using the following settings in your settings file:

```python
# Maximum number of instances to show per model (default: 1)
# Set to 0 to show all instances
WAGTAIL_UNVEIL_MAX_INSTANCES = 1
```

## Command options

The command has a few flags that can be used to adjust the output. The flags are all optional:

- `--base_url`: The base URL to use for the output. Auto generated from the Wagtail site settings.
- `--output`: Output the urls to the console or to a file. Default is console.
- `--file`: The file name to output the urls to. This is only used if the output option is set to file the file type is a simple text file.
- `--max-instances`: The maximum number of instances to show for each URL. This is used to adjust the number of instances shown in the output. The default is 1 a value of 0 will show all instances.


## Running the tests

To run the tests, you need to have the package installed and the virtual environment activated. Then run the following command:

```bash
uv run manage.py test wagtail_unveil
```

## Running tox tests

To run the full test suite across all supported Python and Wagtail/Django versions:

```bash
uv pip install tox tox-uv
tox
```

To run tests for a specific environment:

```bash
tox -e py312-wagtail60-django50
```

Available environments can be listed with:

```bash
tox list
```

You should see the console output for the example_project app urls. The urls are grouped by frontend urls and backend urls. The backend urls are grouped by listing and edit urls.

You will see some urls that indicate (NO INSANCES) which means there are no records avaiable for that url. This is expected as the app is not fully populated with data.