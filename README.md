# Server Eggs

**Server Eggs** is a Discord bot relying on *User-Generated Content*, which is shared around for fun purposes.\
The secondary purpose is to spread servers around through the **Egg**s.

[![Version](https://img.shields.io/github/v/tag/ActuallyFlamey/ServerEggs?sort=semver&label=Version&color=5865f2)]()
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Donate-ff5f5f?logo=kofi)](https://ko-fi.com/hexablue)
[![Support](https://img.shields.io/badge/Support%20Discord-Join-5865f2)](https://discord.gg/G9vfEZGZnT)

# Help us out!

## Donate

Keep **Server Eggs** running! Donate to [**HexaBlue's Ko-fi**](https://ko-fi.com/hexablue)!

## Contribute

View the [**Contribution Guidelines**](./CONTRIBUTING.md) to submit **code** or **translations**!

# Installation

## Install the main instance

To install the main instance of **Server Eggs** in Discord, head to the *App Discovery* page for it: https://discord.com/discovery/applications/886686500845138041

## Run your own instance

Running your own instance of **Server Eggs** will ***NOT*** connect it to the main database. But it can be useful for small projects, like if a content creator wanted to take in submissions from their community and see random ones.

The following guide assumes **Git**, **Python** (>=3.12, 3.14 recommended) and **PostgreSQL** are *already installed* on your target system. If you want to use [`uv`](https://docs.astral.sh/uv/), install it as well.

- **Clone** the repository and enter it.
    ```sh
    git clone https://github.com/ActuallyFlamey/ServerEggs.git
    cd ServerEggs
    ```
- Create a **Python Virtual Environment**
    - You can name it however you like, but I like the name *"eggvironment"*. Because I'm funny.
    - With `venv`:
        ```sh
        python3 -m venv eggvironment
        ```
    - With `uv`:
        ```sh
        uv venv eggvironment
        ```
- **Enter** the **virtual environment**
    ```sh
    source eggvironment/bin/activate
    ```
    - **Note**: on certain shells (such as `fish`), there are special scripts to enter a venv, and the main one *will not work*.
    - **Note**: if you use `uv sync` below, activation is optional since you can run everything with `uv run`.
- **Install** the **dependencies**.
    - With `pip`:
        ```sh
        pip install -r requirements.txt
        ```
    - With `uv` (inside the activated venv):
        ```sh
        uv pip install -r requirements.txt
        ```
    - With `uv` (no activated venv):
        ```sh
        uv sync
        ```
- **Set up** a **PostgreSQL database**.
- **Create a folder** to store **file-based Egg attachments**.
    ```sh
    mkdir media
    ```
- Set the **environment variables**.
    - **Create a file** called `.env` in the root of the folder.
    - **Use [.env.example](https://github.com/ActuallyFlamey/ServerEggs/blob/main/.env.example)** as a guide to the **secret strings** you have to put in it.
- Run the **Tortoise Migrations** to set up the database schema.
    ```sh
    tortoise migrate
    ```
    - With `uv sync` (without an activated venv):
        ```sh
        uv run tortoise migrate
        ```
- If you are **hosting your instance on a server**, set up an appropriate **systemd unit file**.
    - Otherwise, if you're just running it manually:
        ```sh
        python3 main.py
        ```
        - With `uv`:
            ```sh
            uv run python main.py
            ```