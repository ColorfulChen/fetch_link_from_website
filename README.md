# Fetch Links from Website

This project is a Python-based tool that recursively extracts all links from a given website and downloads their content. It categorizes links as valid or invalid and calculates metrics such as valid rate and precision rate.

## Features

- Recursively fetch all links from a website.
- Categorize links into valid and invalid.
- Download content from valid links.
- Generate metrics for valid rate and precision rate.
- Save results in organized directories.

## Setup

1. Clone the repository.
2. Install the required dependencies:

   ```sh
   pip install -r requirements.txt
   ```

## Usage

Run the script with the URL of the website you want to analyze:

```sh
python main.py <website_url>
```

Example:

```sh
python main.py https://www.github.com
```

## Output

The script generates the following outputs in the `result/` directory:

1. **Valid Links**: A file named `valid_link.txt` containing all valid links.
2. **Invalid Links**: A file named `invalid_link.txt` containing all invalid links.
3. **Metrics**: A file named `result.txt` containing the valid rate and precision rate.
4. **Downloaded Content**: A `content/` folder containing the downloaded files.

## Automation with GitHub Actions

The project includes a GitHub Actions workflow to automate the fetching process. The workflow is triggered on:

- Scheduled intervals (cron jobs).
- Manual dispatch.
- Push events.

The workflow is defined in `.github/workflows/main.yml`.

## Example Results

An example of the results is stored in `res.csv`:

| Website                     | Valid Rate | Precision Rate |
|-----------------------------|------------|----------------|
| https://www.github.com      | 0.84       | 1.0            |
| https://en.wikipedia.org    | 0.5454     | 1.0            |
| https://huggingface.co      | 0.158      | 1.0            |

## License

This project is licensed under the MIT License.
```