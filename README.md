<div align="center">
    <h1>wd2tantivy</h1>
    <p>
    A program for generating a <a href="https://github.com/quickwit-oss/tantivy">tantivy</a> index from a Wikidata dump.
    </p>
</div>
<p align="center">
    <img alt="License" src="https://img.shields.io/github/license/cyanic-selkie/wd2tantivy?label=license">
</p>

## Usage

Clone the repository and run the following command to install the package inside of a virtual environment:

```bash
poetry install
```

`wd2tantivy` requires only the compressed (`.gz`) Wikidata truthy dump in the N-Triples format as input. You can download it with the following command:

```
wget https://dumps.wikimedia.org/wikidatawiki/entities/latest-truthy.nt.gz
```

`wd2tantivy` uses [spaCy](https://github.com/explosion/spaCy) to lemmatize the aliases. This means you need to download the [appropriate model](https://spacy.io/models) you wish to use first.

For example:

```bash
poetry run python -m spacy download en_core_web_lg
```

After downloading the dump and the model, you can generate the tantivy index with the following command:

```bash
pigz -dc latest-truthy.nt.gz | \
poetry run wd2tantivy --input latest-truthy.nt.gz \
                      --language "${LANGUAGE}" \
                      --spacy-model "${SPACY_MODEL}" \
                      --output "${OUTPUT_DIR}"
```

Where `${LANGUAGE}` is a [BCP-47](https://en.wikipedia.org/wiki/IETF_language_tag#List_of_common_primary_language_subtags) language code.

The tantivy index will be written into `${OUTPUT_DIR}`.

Each document in the index contains 3 stored and indexed fields:
* `qid` (`integer`)
* preferred `name` (NFC normalized, UTF-8 encoded `text`)
* `alias` (lemmatized, NFC normalized, UTF-8 encoded `text`); this field can have multiple values

## Performance

`wd2tantivy` uses as many threads as there are logical CPU cores. On a dump from March 2023, containing \~100,000,000 nodes, it takes \~5 hours to complete for English with peak memory usage of \~2.5MB on an AMD Ryzen Threadripper 3970X CPU and an SSD.

