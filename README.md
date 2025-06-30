This program can parse car deals from AutoRia, a Ukrainian marketplace for cars.

# Installation

Recommended way to install is to use `poetry`

But, it is also possible to simply run `pip install .`, and it should work.

Of course, always create a virtual environment first.

# Usage

1. Go to https://auto.ria.com and create a search query by selecting some parameters. The end link should start with `https://auto.ria.com/uk/search/?`. Note the total number of offers - it will be important later.

> Note: make sure you are on the old website, not the new one. The new one is not supported.

2. Tweak the values in `carria/__main__.py`:

- `db_name`: name of the database file
- `url`: the link to the search query
- `starting_page`: the page number to start with
- `delay_ms`: delay between requests in milliseconds between requests

3. Run the script (as a module, using `python -m carria`)

4. Wait until the script parses all of the pages. Make sure that the number of cars it prints out (`Total {n} cars in {database}`) is similar to the total number of offers on the website you noted in step 1.

If the numbers are much different, it stopped prematurely. It happens sometimes - just set the starting page to whatever it ended on, and re-start the script. Waiting a little helps. Increasing the delay between requests helps too.

5. Enjoy your duckdb file.