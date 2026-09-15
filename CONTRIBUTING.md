# Server Eggs Contribution Guide

## Contributing Code

To **contribute code** to **Server Eggs**, simply open a [Pull Request](https://github.com/ActuallyFlamey/ServerEggs/pulls)!

We ask that you generally **adhere** to the same **coding style** as the other contributions.

## Contributing Translations

To **help localize Server Eggs** in more languages, head over to [our Weblate page](https://hosted.weblate.org/projects/seggs).

## LLM Contribution Policy

**Server Eggs**'s policy on **LLM contributions** is quite similar to that of the Linux kernel:

LLM contributions are **allowed**, *but*:
- The **human** submitter takes **full responsibility** for the LLM's code, and declares that they **have thoroughly reviewed and tested** the resulting codebase.
- You must **disclose information** about the **LLM that was used** on the **last paragraph** of the **commit message**, and **in your Pull Request text**:
    - The **format** is: `LLM [<amount of help: Assist | Equal | Major>]: <model>, <effort>, <harness>, <inference provider>`
    - Examples:
        ```sh
        git commit -m "feat: added something" -m "LLM [Assist]: Claude Opus 5, Ultracode, Claude Code, Anthropic"
        ```
        ```sh
        git commit -m "ref: refactored utils" -m "LLM [Major]: GLM-5.3, High, OpenCode, OpenRouter"
        ```
        ```sh
        git commit -m "fix: small bug" -m "LLM [Assist]: Qwen3.8 27B, Unrestricted, OpenCode, LMStudio (local)"
        ```
        - *Note: These commit names are just examples. Don't actually name your commits like this.*