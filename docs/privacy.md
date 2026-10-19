# Privacy screening and optional local Presidio procedure

The default validator runs narrow email-like, international-phone-like and URL-like regex checks across all five canonical JSONL files. Reports contain file roles, line numbers and finding types only. They do not include matches, context snippets, free-form reasons or untrusted record IDs. Contact-pattern findings block export until resolved in canonical data and re-reviewed; this small workflow has no automated finding waiver.

These checks miss names, many identifiers, addresses, local-format phone numbers, credentials and semantic sensitivity. They can flag harmless examples or miss sensitive content. Human review is required independently of structural validation and automated screening. Local storage, a virtual environment and synthetic labels do not establish anonymity or legal compliance. Restrict filesystem access and use only the team's approved private storage/version control. No public repository or external upload has been configured.

## Optional Presidio scan — not run

The original raw `validate.py` includes an optional `--presidio` path. It requires already installed `presidio-analyzer`, spaCy and `en_core_web_lg`, configures a local spaCy engine and refuses a missing model. These optional tools are not in `requirements.txt` and were not installed or executed for this setup. The supplied implementation uses threshold 0.5, a pilot setting without a validated privacy guarantee.

If the team chooses this check later:

1. Inspect the supplied optional code and current official package documentation. In a separate environment, deliberately provision trusted compatible package/model distributions. Review their licenses, dependencies and telemetry; record exact versions and local model/configuration hashes. No command in this project downloads them.
2. Disable network access for the scan. Do not enable remote recognizers, external endpoints or dataset-bearing telemetry. Use only local models/recognizers.
3. Copy the original `validate.py` and the **current** three working scenario/question/evaluation JSONL files into a disposable local directory. Run the supplied `validate.py --presidio` there using the separately provisioned interpreter. Do not run it in the raw snapshot. Its `main()` overwrites a report and creates an ungated input export; discard that export and never use it for models or retrieval. The approved `research.py export` remains the only supported export route.
4. The supplied Presidio path scans scenario context and question text only. Separately review evaluation notes, applicability/provenance text and review reasons; the current regex screening covers them, but is not equivalent to a Presidio scan. Never describe this as a complete scan of every field.
5. Save an explicitly named local scan report with canonical dataset hashes, tool/model/configuration versions, threshold, date and completion status. Retain entity type/count/position or safe record references, not matched text. A missing dependency/model means `not_completed`, not a clean result. Do not merge optional results into the default report's `presidio: not_run` field without implementing and verifying that integration.
6. Review false positives and possible false negatives. Revise inappropriate data in working JSONL, document why, and re-review changed records. Do not remove intentional fictional challenge instructions merely because they mention credentials; first determine whether actual sensitive content is present.

No Presidio, security, educational or compliance certification is claimed. The original raw validation report is historical package evidence; the current local result is `reports/validation_report.json`.
